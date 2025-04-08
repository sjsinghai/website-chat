from website_chat.embedder import Embedder
from website_chat.prompts import (
    DOCS_ASSISTANT_SYSTEM_PROMPT_PREFIX,
    NON_RESPONSE,
    CONTEXTUALIZE_QUERY_SYSTEM_PROMPT,
)
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from website_chat.settings import DOC_DIR
from dotenv import load_dotenv

load_dotenv()


class SearchDocs:
    def __init__(self, llm_provider_string: str):
        self.embedder = Embedder(doc_dir=DOC_DIR)
        self.embedder.embed_documents()
        self.last_response = None
        self.llm_provider_string = llm_provider_string
        self.agent = self.build_agent()

    def build_agent(self) -> Agent:
        if self.llm_provider_string.startswith("ollama"):
            model_name = self.llm_provider_string.split(":", 1)[1]
            ollama_model = OpenAIModel(
                model_name=model_name,
                provider=OpenAIProvider(base_url="http://localhost:11434/v1"),
            )
            return Agent(ollama_model)
        return Agent(self.llm_provider_string)

    def set_llm_provider_string(self, llm_provider_string: str):
        self.llm_provider_string = llm_provider_string
        self.agent = self.build_agent()

    @staticmethod
    def get_prompt(context: str, query: str) -> str:
        prompt = f"""{DOCS_ASSISTANT_SYSTEM_PROMPT_PREFIX}

        Context from documents:
        {context}

        Human: {query}

        Assistant:"""
        return prompt

    def contextualize_query(self, query: str) -> str:
        agent = self.build_agent()
        prompt = (
            f"""{CONTEXTUALIZE_QUERY_SYSTEM_PROMPT} <question> {query}</question>"""
        )
        result = agent.run_sync(prompt, message_history=[self.last_response])
        return result.data

    def answer(
        self,
        query: str,
    ) -> tuple[str, str, str]:
        if self.last_response:
            query = self.contextualize_query(query)
        # Get relevant chunks
        context, _ = self.embedder.get_context_for_query(query)
        # get prompt
        if not context:
            response = NON_RESPONSE
            return response, "", context
        prompt: str = self.get_prompt(context, query)

        result = self.agent.run_sync(prompt)
        response = result.data
        self.last_response = result.new_messages()[1]

        return response, prompt, context
