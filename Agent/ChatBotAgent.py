from tools_Agent import *
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
load_dotenv()
from langchain_openai import ChatOpenAI

class ChatBot:
    def __init__(self):
        self.model_llm = ChatOpenAI(
            model= 'gemma-3-1b-it-qat',
            api_key="api_key",  # API key có thể là bất kỳ giá trị nào
            base_url="http://localhost:1234/v1"  # Địa chỉ server LM Studio
        )
        self.check_point = InMemorySaver()
        self.tools = [create_invoice_docx, get_prompt_for_data_excel, read_excel_data]
        self.prompt = 'Bạn là trợ lý ảo cho doanh nghiệp được huấn luyện để có thể thao tác với người dùng. Để tạo hoá đơn từ file .xlsx đầu tiên là đọc file sau đó trích xuất dữ liệu prompt từ tool tạo prompt sau đó đưa dữ liệu thích hợp vào tool tạo hoá đơn đầu ra'
        self.config = {"configurable": {"thread_id": "1"}}
        self.Agent= create_react_agent(model= self.model_llm, tools= self.tools, prompt= self.prompt, checkpointer= self.check_point)
    def chat(self, message: str) -> str:
        input_message = {"role": "user", "content": message}
        res = self.Agent.invoke(input={"messages": [input_message]}, config=self.config)
        return res
