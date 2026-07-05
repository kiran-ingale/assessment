from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI


def load_system_prompt(path: Path = Path("prompts/system_prompt.txt")) -> str:
    return path.read_text(encoding="utf-8")


def build_llm(provider: str, api_key: str, model_name: str, temperature: float = 0.1):
    provider = provider.lower()
    if provider == "openai":
        return ChatOpenAI(model=model_name, api_key=api_key, temperature=temperature)
    if provider == "gemini":
        return ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key, temperature=temperature)
    raise ValueError(f"Unsupported provider: {provider}")


def make_tools(retriever, *, allow_web_search: bool) -> list:
    @tool
    def retrieve_documents(query: str) -> str:
        """Search uploaded/local documents in ChromaDB and return cited snippets."""
        docs = retriever.invoke(query)
        if not docs:
            return "No matching document context found."

        snippets = []
        for idx, doc in enumerate(docs, start=1):
            source = doc.metadata.get("source", "unknown document")
            page = doc.metadata.get("page")
            chunk_id = doc.metadata.get("chunk_id", idx)
            label = f"{source}"
            if page is not None:
                label += f", page {int(page) + 1}"
            label += f", chunk {chunk_id}"
            text = " ".join(doc.page_content.split())
            snippets.append(f"[DOC-{idx}: {label}]\n{text}")
        return "\n\n".join(snippets)

    tools = [retrieve_documents]

    if allow_web_search:
        search = DuckDuckGoSearchRun()

        @tool
        def web_search(query: str) -> str:
            """Search the public web for current or missing information."""
            result = search.invoke(query)
            if not result:
                return "No web search results found."
            return f"[WEB-1: DuckDuckGo search results for '{query}']\n{result}"

        tools.append(web_search)

    return tools


class ResearchAgent:
    def __init__(self, *, llm, tools: list, system_prompt: str, max_iterations: int = 5):
        self.llm = llm.bind_tools(tools)
        self.tools_by_name = {item.name: item for item in tools}
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        messages = [SystemMessage(content=self.system_prompt)]
        messages.extend(inputs.get("chat_history", []))
        messages.append(HumanMessage(content=inputs["input"]))
        intermediate_steps = []

        for _ in range(self.max_iterations):
            ai_message = self.llm.invoke(messages)
            messages.append(ai_message)
            tool_calls = getattr(ai_message, "tool_calls", None) or []

            if not tool_calls:
                return {"output": ai_message.content, "intermediate_steps": intermediate_steps}

            for call in tool_calls:
                tool_name = call.get("name")
                tool_args = call.get("args", {})
                call_id = call.get("id")
                selected_tool = self.tools_by_name.get(tool_name)

                if selected_tool is None:
                    tool_output = f"Tool '{tool_name}' is not available."
                else:
                    tool_output = selected_tool.invoke(tool_args)

                intermediate_steps.append({"tool": tool_name, "tool_input": tool_args})
                messages.append(
                    ToolMessage(
                        content=str(tool_output),
                        tool_call_id=call_id or f"{tool_name}-call",
                    )
                )

        return {
            "output": "I don't know based on the available sources.",
            "intermediate_steps": intermediate_steps,
        }


def build_agent_executor(
    *,
    provider: str,
    api_key: str,
    model_name: str,
    retriever,
    allow_web_search: bool,
    system_prompt: str,
) -> ResearchAgent:
    llm = build_llm(provider=provider, api_key=api_key, model_name=model_name)
    tools = make_tools(retriever, allow_web_search=allow_web_search)
    return ResearchAgent(llm=llm, tools=tools, system_prompt=system_prompt)


def run_research(
    *,
    executor: ResearchAgent,
    topic: str,
    chat_history: List[BaseMessage],
) -> Dict[str, Any]:
    result = executor.invoke({"input": topic, "chat_history": chat_history})
    chat_history.extend([HumanMessage(content=topic), AIMessage(content=result["output"])])
    return result


def summarize_tool_calls(result: Dict[str, Any]) -> list:
    calls = []
    for step in result.get("intermediate_steps", []):
        tool_name = step.get("tool", "tool")
        tool_input = step.get("tool_input", "")
        calls.append(f"{tool_name}: {tool_input}")
    return calls
