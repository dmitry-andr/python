import os

from dotenv import load_dotenv
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.llm.core.prompt_loader import load_prompt


#switch to another model
#from langchain_ollama import ChatOllama
#self.llm = ChatOllama(model="llama3.1")

load_dotenv()


class LLMService:

    def __init__(self):

        self.llm = ChatOpenAI(
            model="gpt-4.1-mini",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        # Load system prompt from file
        self.system_prompt = load_prompt("system.md")

        # Create reusable prompt template
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("human", "{message}"),
            ]
        )

        # Compose prompt + model into a chain
        self.chain = self.prompt | self.llm

    def ask(self, message: str) -> str:

        response = self.chain.invoke(
            {
                "message": message,
            }
        )

        return response.content


llm_service = LLMService()