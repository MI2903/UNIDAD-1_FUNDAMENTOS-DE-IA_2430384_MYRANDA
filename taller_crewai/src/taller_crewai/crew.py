from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.llm import LLM
from crewai_tools import SerperDevTool

# Modelo de Gemini (en la nube, sin instalar nada local)
llm_gemini = LLM(
    model="gemini/gemini-3.5-flash-lite",
)

# Herramienta de búsqueda en Google
search_tool = SerperDevTool()


@CrewBase
class TallerCrewai():
    """TallerCrewai crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def investigador_tecnologias(self) -> Agent:
        return Agent(
            config=self.agents_config['investigador_tecnologias'],
            verbose=True,
            llm=llm_gemini,
            tools=[search_tool]
        )

    @agent
    def redactor_informe(self) -> Agent:
        return Agent(
            config=self.agents_config['redactor_informe'],
            verbose=True,
            llm=llm_gemini
        )

    @task
    def tarea_investigacion(self) -> Task:
        return Task(
            config=self.tasks_config['tarea_investigacion'],
        )

    @task
    def tarea_redaccion(self) -> Task:
        return Task(
            config=self.tasks_config['tarea_redaccion'],
            output_file='informe.md'
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            max_rpm=10,
        )