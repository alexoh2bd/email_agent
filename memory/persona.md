# Recipient persona (for tone critique)

You are reviewing email drafts intended for High Profile Researchers: Professors, Post-Docs, and PhD students.

- Prefers **clear, concrete updates** over long preambles.
- Tone: **professional but warm** — not stiff corporate, not casual Slack.
- Appreciates **bullet points** for status and next steps when listing work items.
- Usually signs off with something like "Thanks" or "Best" — mirror that level of formality in replies to them.
- Dislikes vague promises; wants **dates or time windows** when scheduling is discussed.

When critiquing a draft, flag: mismatched formality, missing facts, vague scheduling, or tone that sounds robotic.

Conversation Titles should be inquisitive and simple to catch the recipient's attention. For Example:
 - "Quick Question about ..."
 - "



 Based on this conversation and everything in your memory, here's a research persona:


# Alexander Oh — Research Persona

## Who I Am

I'm a Master's student in AI at Duke University's Pratt School of Engineering, graduating in August 2026, and a researcher in the Duke NLP Lab. My work sits at the intersection of self-supervised learning, world models, and embodied intelligence. The central question I keep returning to is deceptively simple: **how do machines learn to understand the physical world the way humans do — not by memorizing patterns, but by learning what matters and how it changes?**

## What I Actually Work On

My research has two tracks that are converging.

The first is **representation learning for visual understanding.** I've been deep in JEPA-style architectures — specifically investigating the shift from generative pixel reconstruction to predictive latent-space learning. I pioneered a semantically guided view selection pipeline for JEPA training that yields 8%+ accuracy gains on few-shot transfer benchmarks (DTD, Food101, CIFAR100), and developed a hybrid contrastive + SIGReg (LeJEPA) framework that achieves +6% top-1 accuracy on ImageNet-100 over MSE baselines. The core insight driving this work: a model doesn't need to reconstruct the world to understand it — it needs to learn what is invariant, what is predictable, and what is causally meaningful.

The second track is **self-supervised reinforcement learning for physical agents.** In JaxGCRL experiments on humanoid locomotion environments, I investigated whether SIGReg alone could replace contrastive learning in a critic-actor architecture. The short answer: it couldn't. But the longer answer — that InfoNCE forces discriminative pressure that SIGReg lacks — taught me something fundamental about what a good objective function actually does to a latent space. Combining both losses let me collapse a dual-encoder architecture to a single encoder with no performance loss, cutting training wall time by 24%.

I also co-developed **ArXivDoc**, a multimodal retrieval benchmark across 8,210 scientific documents with 547 evidence-grounded queries spanning text, tables, and figures — which is now under review at COLM 2026. And I built **LeDEEP**, a monocular depth estimation model using LeJEPA that achieves a 37% reduction in AbsRel error over baselines and a 20x CPU inference speedup via resolution-reduction — demonstrating that SSL-trained representations transfer meaningfully to real perception tasks.

## What I'm Trying to Do (The Bigger Picture)

The thread connecting everything I do is a belief that **the path to general intelligence runs through physical world models** — systems that learn structured, predictive representations of reality rather than task-specific features trained on supervised labels.

I want to work at the frontier of that problem. Concretely, that means:

- **Short term:** Secure a research lab affiliation at UC Berkeley or Stanford in world models, JEPA, or general perception — ideally working with PhD students and postdocs in labs like RAIL, KAIR, or Wu's Physical Intelligence Group at Stanford. My summer internship at Huma AI (San Francisco, hybrid) gives me a Bay Area base from which to build those relationships in person.
- **Medium term:** Submit my two in-progress papers (JEPA semantically-guided view selection, ArXivDoc multimodal retrieval) and establish a credible research track record before transitioning to a PhD program or full-time research role.
- **Long term:** Work on the hard, open problems in learning physical world models — closing the gap between what works in simulation and what works in reality, and building AI systems that can reason about the world at the level of abstraction that makes them genuinely useful for embodied agents.

## How I Think About Research

My methodology is consistent across projects: **define what "good" looks like first, find what already exists, evaluate it rigorously for the specific problem, then improve.** This evaluation-first orientation is deliberate. It's easy to build things. It's harder to know whether what you built actually works and why.

I approach research the way you approach a physical system — by reproducing, breaking, and rebuilding the state-of-the-art until you understand what's actually load-bearing. The SIGReg vs. contrastive ablation in my RL work is a good example: the result was null, but the null result was informative. That's what I care about.

## How I Position Myself

I'm not a pure theorist and I'm not a pure engineer. I'm most comfortable in the space between — designing experiments that expose structural truths about learning systems, building infrastructure to run them at scale, and connecting empirical findings to the broader questions in AI about how representations should be organized. I've worked in PyTorch and JAX, on Slurm clusters and GCP, with contrastive objectives and diffusion-based policies, on vision tasks and language retrieval benchmarks.

The role I'm looking for — as a collaborator in a Bay Area research lab this summer — is one where I can contribute meaningfully to ongoing experiments while learning from researchers who are closer to the frontier than I am. I bring technical rigor, genuine intellectual curiosity about the hard problems, and a willingness to do the unsexy work of ablations, benchmarks, and baselines that good research actually requires.

---

Want me to trim this down into a shorter version (e.g. a 150-word bio or a one-paragraph "research statement" version for outreach)?
