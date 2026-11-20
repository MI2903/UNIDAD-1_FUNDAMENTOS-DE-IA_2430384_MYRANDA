from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.llm import LLM
from crewai_tools import SerperDevTool

# Modelo de Gemini (en la nube, sin instalar nada local)
llm_gemini = LLM(
    model="gemini/gemini-3.5-flash-lite",
)

# Herramienta de busqueda en Google (10 resultados por busqueda)
search_tool = SerperDevTool(n_results=10)


@CrewBase
class NoticiasAndes1972():
    """Equipo de agentes que investiga, redacta y publica noticias"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def investigador_historico(self) -> Agent:
        return Agent(
            config=self.agents_config['investigador_historico'],
            verbose=True,
            llm=llm_gemini,
            tools=[search_tool]
        )

    @agent
    def redactor_noticias(self) -> Agent:
        return Agent(
            config=self.agents_config['redactor_noticias'],
            verbose=True,
            llm=llm_gemini
        )

    @agent
    def editor_publicador(self) -> Agent:
        return Agent(
            config=self.agents_config['editor_publicador'],
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
            output_file='noticias.md'
        )

    @task
    def tarea_publicacion(self) -> Task:
        return Task(
            config=self.tasks_config['tarea_publicacion'],
            output_file='index.html'
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