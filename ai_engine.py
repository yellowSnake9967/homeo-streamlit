import os
import certifi
from dotenv import load_dotenv

from langchain_tavily import TavilySearch
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# ---------- ENV & SSL ----------
load_dotenv()
os.environ["SSL_CERT_FILE"] = certifi.where()

# ---------- LLM ----------
def build_agent():
    #model = ChatOpenAI(model="gpt-5-nano")
    model = ChatOpenAI(model="gpt-4.1-nano", temperature=0)
    
    tavily_tool = TavilySearch(
        max_results=3,
        #topic="general",
        search_depth="advanced", # advanced , basic
        chunks_per_source=2,              # 🔹 CHANGED (3 → 2)
        #include_raw_content="markdown",
        include_answer=False,
        include_domains=["homeoint.org/books"]
    )
    
    agent = create_agent(
        model=model,
        tools=[tavily_tool]
    )
    return agent


def run_query(user_input: str) -> str:
    agent = build_agent()
    user_input = user_input.strip()
    prompt = f"""
You are a careful, evidence-focused research assistant specialized in classical homeopathic materia medica.

You will be given a clinical description (symptoms, modalities, mental/emotional state).

You must perform at least one search using the provided search tool before answering.

Your task:

1) Search ONLY the domain http://www.homeoint.org/books/ (use: site:homeoint.org/books).
   - Do NOT use prior knowledge or external sources.
   - Do NOT include any remedy that is not explicitly found on pages under /books/.
   - Any page not under /books/ must be ignored, even if returned by the search tool.

2) From the materia medica pages you find, extract candidate remedies that closely match the given case.
   For each remedy, extract:
   - Remedy name
   - Exact symptom phrases that match the case (quote verbatim, max 20 words per quote)
   - A short reasoning line (1–2 sentences) explicitly connecting the quoted symptoms to the patient's presentation
   - Confidence score (High / Medium / Low), defined as:
        • High: at least 2 mental/emotional symptoms AND at least 1 general modality (time, temperature, motion) clearly match, with all quotes directly mapping to the QUERY
        • Medium: clear similarity but missing either mental dominance or general modality
        • Low: only general or local resemblance

   If a quoted symptom directly contradicts the QUERY (opposite desire, modality, or polarity), the remedy must be excluded entirely.

3) Provide references for every quote:
   - Full page title
   - Exact URL from homeoint.org/books/

4) If no strong or medium-confidence matches are found:
   - Clearly state this
   - Suggest precise next steps (keywords to search, related remedy families, or additional modalities to clarify)

Formatting requirements:
- Provide a ranked list of up to 5 remedies (1 = best match).
- If fewer than 3 remedies meet Medium or High confidence, list only those found.
- Do NOT include a remedy with Low confidence unless fewer than 3 remedies qualify.
- For each remedy include, in this order:
    **Remedy name**
    - Matching symptoms (quoted)
    - Short reasoning
    - Confidence
    - Reference URL
- End with a short summary (2–3 bullet points) explaining why the top remedy ranked highest.

Be precise, conservative, and citation-driven.
Do not speculate beyond what is supported by the cited materia medica text.

QUERY:
{user_input}
"""
    prompt = prompt.strip()
    res = agent.invoke({"messages": prompt})
    '''print("#"*50)
    print(res)
    print("#"*50)'''
    return res["messages"][-1].content

