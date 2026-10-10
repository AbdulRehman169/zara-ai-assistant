import os
from dotenv import load_dotenv
from crewai_tools import TavilySearchTool
from crewai import Agent, Task, Crew, Process, LLM
load_dotenv()
search_tool = TavilySearchTool(api_key=os.getenv("TAVILY_API_KEY"))
zara_llm = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY")
)
researcher = Agent(
    role="Senior Research Analyst",
    goal="Find accurate, up-to-date facts about {topic}",
    backstory=(
        "You are Zara's research specialist. You are meticulous, you never "
        "make things up, and you always note where a fact comes from."
    ),
    tools=[search_tool],
    llm=zara_llm,
    verbose=True,
    allow_delegation=False,
)
planner = Agent(
    role="Content Planner",
    goal="make a clear content plan/outline for {topic} for a chosen audience (like beginners).",
    backstory=(
        "You are Zara's planner. You create structured outlines for content "
        "that is easy for beginners to follow."
    ),
    llm=zara_llm,
    verbose=True,
    allow_delegation=False,# allow delegation is set to False to ensure the planner does not delegate tasks to other agents
)
writer = Agent(
    role="Content Writer",
    goal="Turn raw research into clear, beginner-friendly content",
    backstory=(
        "You are Zara's writer. You explain complex topics in plain English "
        "so a total beginner can understand them."
    ),
    llm=zara_llm,
    verbose=True,
    allow_delegation=False,
)
editor = Agent(
    role="Content Editor",
    goal="Ensure the content is clear, accurate, and beginner-friendly",
    backstory=(
        "You are Zara's editor. You check for clarity, accuracy, and "
        "ensure the content is suitable for beginners."
    ),
    llm=zara_llm,
    verbose=True,
    allow_delegation=False,
)
research_task = Task(
    description=(
        "Research the topic: {topic}.\n"
        "Collect the 5 most important and current facts a beginner "
        "should know. Prioritise accuracy over quantity."
    ),
    expected_output=(
        "A numbered list of exactly 5 facts about {topic}. "
        "Each fact is one clear sentence, followed by a short 'why it matters' note."
    ),
    agent=researcher,
)
planner_task = Task(
    description=(
        "Create a content plan for an article about {topic} for beginners. "
        "Use the research provided."
    ),
    expected_output=(
        "A clear outline for a 3-paragraph article:\n"
        "  - Para 1: what {topic} is\n"
        "  - Para 2: why it matters\n"
        "  - Para 3: one real-world example"
    ),
    agent=planner,
    context=[research_task],
)
write_task = Task(
    description=(
        "Using ONLY the research provided, write a short article about {topic} "
        "for an absolute beginner. Keep it friendly and jargon-free."
    ),
    expected_output=(
        "A 3-paragraph article in plain English:\n"
        "  - Para 1: what {topic} is\n"
        "  - Para 2: why it matters\n"
        "  - Para 3: one real-world example"
    ),
    agent=writer,
    context=[research_task, planner_task], 
    output_file="zara_article.md",
)
editor_task = Task(
    description=(
        "Edit the article for clarity, accuracy, and beginner-friendliness. "
        "Make sure it is jargon-free and easy to read."
    ),
    expected_output=(
        "A revised version of the article that is clear, accurate, and "
        "suitable for beginners."
    ),
    context=[write_task],
    output_file="zara_article_final.md",
    agent=editor,
)

content_crew = Crew(
    agents=[researcher, planner, writer, editor],
    tasks=[research_task, planner_task, write_task, editor_task],
    process=Process.sequential,   
    verbose=True,
)
if __name__ == "__main__":
    result = content_crew.kickoff(inputs={"topic": "Agentic AI"})
    print("\n\n================ FINAL RESULT ================\n")
    print(result)