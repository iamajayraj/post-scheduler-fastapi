from typing import TypedDict, Dict, Any, List
import os, requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from string import Template
from datetime import date, time

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ——— Load your prompt templates ———
with open("post_generator_agent_prompt.txt") as f:
    gen_tpl = Template(f.read())

with open("post_finetune_prompt.txt") as f:
    tune_tpl = Template(f.read())


# ——— 1. Define shared state ———
class PostState(TypedDict, total=False):
    id: int
    date: str
    time: str
    topic: str
    context: str
    tone: str
    cta: str
    status: str
    output_post: str
    feedback: str
    approved: bool
    platform: str
    messages: List[Any]  # List[BaseMessage]


# ——— 2. Define nodes ———

def ai_generate(state: PostState) -> PostState:
    prompt = gen_tpl.substitute(
        topic=state['topic'],
        context=state['context'],
        tone=state['tone'],
        cta=state['cta']
    )
    llm = ChatOpenAI(model="gpt-4o-mini")
    res = llm.invoke([SystemMessage(content=prompt)])
    state["output_post"] = res.content.strip()
    return state


def ai_refine(state: PostState) -> PostState:
    if state["approved"] == True:
        supa = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        payload = {
        "date": state['date'],
        "time": state["time"],
        "topic": state["topic"],
        "context": state["context"],
        "tone": state["tone"],
        "cta": state["cta"],
        "post": state["output_post"],
        "status": state["status"],
        }

        res = requests.post(
        f"{supa}/rest/v1/scheduled-posts",
        json=payload,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        )
        res.raise_for_status()
        return state
    
    # Init message history if needed
    else:
        if "messages" not in state or not state["messages"]:
                system_prompt = tune_tpl.substitute(
                    topic=state['topic'],
                    context=state['context'],
                    tone=state['tone'],
                    cta=state['cta']
                )
                state["messages"] = [SystemMessage(content=system_prompt)]
                state["messages"].append(AIMessage(content=state["output_post"]))

        # Add feedback
        state["messages"].append(HumanMessage(content=state["feedback"]))

        # LLM call
        llm = ChatOpenAI(model="gpt-4o-mini")
        res = llm.invoke(state["messages"])

        # Update post + memory
        new_post = res.content.strip()
        state["output_post"] = new_post
        state["messages"].append(AIMessage(content=new_post))
        return state


# ——— 3. Build Graphs ———

def build_generate_graph():
    builder = StateGraph(PostState)
    builder.add_node("AIWritePost", ai_generate)
    builder.set_entry_point("AIWritePost")
    builder.add_edge("AIWritePost", END)
    return builder.compile()


def build_feedback_graph():
    builder = StateGraph(PostState)
    builder.add_node("AIRefine", ai_refine)
    builder.set_entry_point("AIRefine")
    builder.add_edge("AIRefine", END)
    return builder.compile()


"""initial_state = {
        "id": 123,
        "date": "2025-07-06",
        "time": "14:30:00",
        "topic": "Self Belief",
        "context": "Why believing in yourself matters",
        "tone": "Encouraging",
        "cta": "Share your story below",
        "approved":True,
        "status": "Queued"
    }

gen_graph = build_generate_graph()
state_after_gen = gen_graph.invoke(initial_state)
print("=== After AI Generate ===")
print("Output Post:", state_after_gen["output_post"])
print(state_after_gen)
print()
fb_graph = build_feedback_graph()
state_after_feedback = fb_graph.invoke(state_after_gen)
print("=== After Feedback Loop ===")
print("Final Approved:", state_after_feedback["approved"])
print("Final Post:", state_after_feedback["output_post"])
print()"""
