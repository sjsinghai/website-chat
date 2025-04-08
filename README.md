Website chat allows you to chat with contents of any website locally.

## Motivation
I am frequently interested in consuming the contents of a website and not just a single webpage for example the
documentation of different projects, in a chat like interface. I have found that chatgpt (and others) sometime lack the
deep and/or latest knowledge of  a particular feature/content. Also I also like to use locally hosted models through ollama
(https://ollama.com).

## Installation
`pip install git+https://github.com/sjsinghai/website-chat.git`

## Usage
- With cloud providers:
<pre>
# add your API key to the environment variable
> export GEMINI_API_KEY=your_key
# use the website-chat command to start a chat session
> website-chat  -u https://docs.sentry.io/platforms/python/  -llm 'google-gla:gemini-2.0-flash'
Crawling website...
[INIT].... → Crawl4AI 0.5.0.post8
Building index ...
ChatBot: Hello! I was able to crawl and index 1 pages.  I'm here to answer any questions about them. Type 'exit' to end the
conversation.
You (Type 'exit' to end chat): concise summary of the article
ChatBot:
Here's a summary of the article about woodpecker drumming:

 • 🪵 Woodpeckers drum to communicate, similar to how songbirds sing. This is especially noticeable from March to June.
 • 🔊 Drumming is a fast, extended sequence of loud pecks, used to advertise territory and attract mates.
 • 🥁 There are three main drumming patterns:
    • Rat-a-tat-tat: Steady, evenly spaced drumming where speed and duration help identify the species. For example, Hairy
      Woodpeckers drum faster than Downy Woodpeckers.
    • Stutterstep Rhythms: Sapsuckers have a complex, recognizable rhythm with an introductory roll followed by unevenly spaced
      beats.
    • Fadeaways: Drumming that trails off at the end, like that of the Pileated Woodpecker.
You (Type 'exit' to end chat): what do you mean trails off at the end?
ChatBot:
Here's what "trail off at the end" means for woodpecker drumming, based on the documentation!

When a woodpecker's drumming "trails off at the end," it means the drumming

 • Speeds up slightly at the end!
 • The volume often decreases, creating a fadeaway effect! ✨

This pattern is characteristic of the Black-backed Woodpecker and the American Three-toed Woodpecker!

You (Type 'exit' to end chat): exit
ChatBot: Goodbye!
</pre>
- With local models:
<pre>
# run the ollama model server
> ollama run gemma3:4b
# use the website-chat command to start a chat session
> website-chat  -u https://docs.sentry.io/platforms/python/  -llm 'ollama:gemma3:4b'
</pre>
- Other options:
`website-chat --help`

## Details
- Under the hood,  `crawl4ai` is used to crawl the website.
- The crawled webpages are saved as markdown files.
- A RAG (retrieval-augmented generation) approach is then used to answer the user query over the saved documents wherein:
  - The saved markdown files are chunked up and embeddings are created for chunks
  - The user query is embedded and semantic similarity is calculated between the user query and the chunks to find the most relevant files.
  - The relevant content is then fed as context to the LLM to get an answer.
