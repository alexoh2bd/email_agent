"""Two-node email drafting agent: Architect (research) then Wordsmith (draft), CLI-first."""

from __future__ import annotations
import os
import argparse
import sys
from pathlib import Path

# Allow `python path/to/agent.py` from repo root: resolve imports from this directory
_SRC = Path(__file__).resolve().parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
    import os

# import vertexai
from dotenv import load_dotenv
# from vertexai.generative_models import GenerativeModel, Part
from google import genai 
from google.genai import types

import config
from prompts import CRITIC_SYSTEM_PROMPT, DRAFT_PROMPT, RESEARCH_PROMPT
from state import initial_state
from tools import build_tool_handlers

load_dotenv()




def _fc_args_to_dict(fc) -> dict:
    raw = getattr(fc, "args", None)
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    if hasattr(raw, "items"):
        return dict(raw.items())
    return {}

def run_tool_loop(
    chat, # This is now a google.genai.chats.Chat object
    state: dict,
    dispatch: dict,
    exit_tool_name: str,
    initial_message: str,
    max_turns: int,
    nudge_message: str,
) -> None:
    """Drive the model until it calls `exit_tool_name` or max turns."""
    
    # 1. Start the loop by sending the initial prompt to the Chat session
    response = chat.send_message(initial_message)
    turns = 0
    
    while turns < max_turns:
        if response.function_calls:
            function_responses = []
            exit_requested = False
            
            for fc in response.function_calls:
                name = fc.name
                kwargs = _fc_args_to_dict(fc)
                print(f"  Tool: {name}({kwargs})")
                
                # 2. Look up the correct function using the dispatch dict
                handler = dispatch.get(name)
                
                if not handler:
                    api_response = {"error": f"Tool '{name}' not found in dispatch."}
                else:
                    try: 
                        # Execute the tool
                        api_response = handler(**kwargs)
                        
                        # Ensure the response is a dictionary for the SDK
                        if not isinstance(api_response, dict):
                            api_response = {"result": str(api_response)}
                    except Exception as e:
                        api_response = {"error": f"Tool Execution Error: {str(e)}. Please adjust your arguments and try again."}
                
                if name == exit_tool_name:
                    exit_requested = True
                    
                # 3. Format the response as a Part
                function_responses.append(
                    types.Part.from_function_response(
                        name=name, 
                        response=api_response 
                    )
                )
            
            # Send the tool outputs back to the model to continue the generation
            response = chat.send_message(function_responses)
            
            if exit_requested:
                return
                
            turns += 1
            continue
            
        # If no tool was called but we haven't exited, nudge the model
        turns += 1
        response = chat.send_message(nudge_message)
        
    raise RuntimeError(
        f"Exceeded max tool turns ({max_turns}) without calling {exit_tool_name}."
    )

def research_node(state: dict, client: genai.Client, model_name: str, arch_config: types.GenerateContentConfig, architect_dispatch: dict) -> None:
    print("\n--- Node 1: Architect (research) ---\n")
    
    # Create an active Chat session for this node
    chat = client.chats.create(
        model=model_name,
        config=arch_config
    )
    
    initial = (
        f"User task:\n{state['user_task']}\n\n"
        "Use tools to gather memory and grounding facts, then submit_strategy_plan."
    )
    
    run_tool_loop(
        chat=chat, # Pass the chat session
        state=state,
        dispatch=architect_dispatch, # Pass the dictionary mapping
        exit_tool_name="submit_strategy_plan",
        initial_message=initial,
        max_turns=config.MAX_ARCHITECT_TURNS,
        nudge_message=(
            "You must use the available tools. "
            "When research is complete, call submit_strategy_plan with your bulleted plan."
        ),
    )

def draft_node(state: dict, client: genai.Client, model_name: str, draft_config: types.GenerateContentConfig, draft_dispatch: dict) -> None:
    print("\n--- Node 2: Wordsmith (draft) ---\n")
    
    chat = client.chats.create(
        model=model_name,
        config=draft_config
    )
    
    plan = state.get("strategy_plan") or "(no plan)"
    initial = (
        f"User task:\n{state['user_task']}\n\n"
        f"Strategic plan from Architect:\n{plan}\n\n"
        "Write and refine the email using the tools, then finalize_draft."
    )
    
    run_tool_loop(
        chat=chat,
        state=state,
        dispatch=draft_dispatch,
        exit_tool_name="finalize_draft",
        initial_message=initial,
        max_turns=config.MAX_ARCHITECT_TURNS,
        nudge_message=(
            "You must use the available tools. "
            "When drafting is complete, call finalize_draft."
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Two-node Gemma email drafting agent (Vertex AI).")
    parser.add_argument(
        "--task",
        type=str,
        help="What the email should accomplish (e.g. schedule meeting with advisor).",
    )
    args = parser.parse_args()
    task = args.task
    if not task:
        task = sys.stdin.read().strip() if not sys.stdin.isatty() else input("Describe the email task: ").strip()
    if not task:
        print("Error: provide --task or pipe text on stdin.", file=sys.stderr)
        sys.exit(1)

    if not config.PROJECT_ID:
        print("Error: set PROJECT_ID in .env or environment.", file=sys.stderr)
        sys.exit(1)

    state = initial_state(task)
    model_name = config.MODEL_NAME 

    # Initialize the single GenAI client
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # We just pass the client to the tools; they can instantiate generate_content calls themselves
    architect_tools_list, draft_tools_list = build_tool_handlers(state, client)
    
    # Create the string-to-function mapping dictionaries required for run_tool_loop
    architect_dispatch = {f.__name__: f for f in architect_tools_list}
    draft_dispatch = {f.__name__: f for f in draft_tools_list}

    arch_config = types.GenerateContentConfig(
        tools=architect_tools_list, # SDK needs the list of callables
        system_instruction=RESEARCH_PROMPT,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        ),
    ) 
    
    draft_config= types.GenerateContentConfig(
        tools=draft_tools_list,
        system_instruction=DRAFT_PROMPT,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True 
        ),
    )

    research_node(state, client, model_name, arch_config, architect_dispatch)
    draft_node(state, client, model_name, draft_config, draft_dispatch)

    print("\n--- Final draft (Pass / Reject in your UI) ---\n")
    print(state.get("draft", "").strip() or "(empty draft)")
    print()


if __name__ == "__main__":
    main()
