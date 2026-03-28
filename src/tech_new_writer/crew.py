from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent

from tech_new_writer.skills import build_skill_backstory

@CrewBase
class TechNewWriter():
    """TechNewWriter crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def trend_researcher(self) -> Agent:
        config = dict(self.agents_config['trend_researcher'])  # type: ignore[index]
        config['backstory'] = f"{config['backstory']}\n\n{build_skill_backstory('trend_researcher')}"
        return Agent(
            config=config,
            verbose=True
        )

    @agent
    def sme(self) -> Agent:
        config = dict(self.agents_config['sme'])  # type: ignore[index]
        config['backstory'] = f"{config['backstory']}\n\n{build_skill_backstory('sme')}"
        return Agent(
            config=config,
            verbose=True
        )

    @agent
    def seo_specialist(self) -> Agent:
        config = dict(self.agents_config['seo_specialist'])  # type: ignore[index]
        config['backstory'] = f"{config['backstory']}\n\n{build_skill_backstory('seo_specialist')}"
        return Agent(
            config=config,
            verbose=True
        )

    @agent
    def content_writer(self) -> Agent:
        config = dict(self.agents_config['content_writer'])  # type: ignore[index]
        config['backstory'] = f"{config['backstory']}\n\n{build_skill_backstory('content_writer')}"
        return Agent(
            config=config,
            verbose=True
        )

    @agent
    def editor(self) -> Agent:
        config = dict(self.agents_config['editor'])  # type: ignore[index]
        config['backstory'] = f"{config['backstory']}\n\n{build_skill_backstory('editor')}"
        return Agent(
            config=config,
            verbose=True
        )

    @task
    def trend_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['trend_research_task'], # type: ignore[index]
        )

    @task
    def technical_review_task(self) -> Task:
        return Task(
            config=self.tasks_config['technical_review_task'], # type: ignore[index]
        )

    @task
    def seo_planning_task(self) -> Task:
        return Task(
            config=self.tasks_config['seo_planning_task'], # type: ignore[index]
        )

    @task
    def article_writing_task(self) -> Task:
        return Task(
            config=self.tasks_config['article_writing_task'], # type: ignore[index]
            output_file='draft_article.md'
        )

    @task
    def final_edit_task(self) -> Task:
        return Task(
            config=self.tasks_config['final_edit_task'], # type: ignore[index]
            output_file='final_article.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the TechNewWriter crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
