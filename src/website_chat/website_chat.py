import asyncio
import shutil
import logging
import os
import sys
from rich.prompt import Prompt

import click
from rich.console import Console
from rich.markdown import Markdown
from website_chat.search_docs import SearchDocs
from website_chat.settings import DOC_DIR
from website_chat.crawl_and_save_results import save_website_to_docs

console = Console()
logger = logging.getLogger(__name__)


class WebsiteChat:
    def __init__(
        self,
        urls: list[str],
        max_pages=200,
        llm_provider_string: str = "ollama:gemma3:1b",
        use_cache=False,
    ):
        self._input_urls = urls
        sys.stdout.write("Crawling website...\n")
        self.cleanup_doc_dir()
        self.saved_urls = asyncio.run(save_website_to_docs(urls, max_pages))
        sys.stdout.flush()
        sys.stdout.write("Building index ...\n")
        self.ask_docs = SearchDocs(llm_provider_string)
        sys.stdout.flush()

    def answer(self, query: str):
        return self.ask_docs.answer(query)[0]

    def chat(self):
        console.print(
            f"ChatBot: Hello! I was able to crawl and index {len(self.saved_urls)} pages.  I'm here to answer any questions about them. Type 'exit' to end the conversation.",
            style="bold blue",
        )
        while True:
            user_input = Prompt.ask(
                "[bold green]You (Type 'exit' to end chat)[/bold green]"
            )
            if user_input.lower() == "exit":
                console.print("ChatBot: Goodbye!", style="bold blue")
                break
            response = Markdown(self.answer(user_input))
            console.print("ChatBot:", style="bold blue")
            console.print(response)

    def cleanup_doc_dir(self):
        target_dir = DOC_DIR
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)


@click.command()
@click.option("--urls", "-u", required=True, multiple=True, help="URLs to crawl")
@click.option("--max_pages", "-m", default=200, help="Max pages to crawl per url")
@click.option(
    "--llm",
    "-llm",
    required=True,
    help="LLM string e.g. `openai:gpt-4o`. Supported formats https://ai.pydantic.dev/api/models/base/#pydantic_ai.models.KnownModelName ",
)
def main(urls, max_pages, llm):
    chat = WebsiteChat(urls, max_pages, llm)
    chat.chat()


if __name__ == "__main__":
    main()
