from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import ast
from tools import make_file_txt, make_file_docx, make_invoice

class ChatBot:
    def __init__(self):
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
        self.llm_with_tools = llm.bind_tools([make_file_txt, make_file_docx, make_invoice])

        self.memory = ConversationBufferMemory(memory_key= "history", return_messages=True)

        prompt = ChatPromptTemplate([
            ('system', "Bạn là một trợ lý ảo, bạn có thể tạo file txt và docx với nội dung được cung cấp."),
            MessagesPlaceholder(variable_name= 'history'),
            ("human", '{input}')
        ])
        # Kết hợp prompt với LLM và tools   
        self.chain = prompt | self.llm_with_tools

    def process_tool_calls(self, ai_msg: AIMessage, memory: ConversationBufferMemory) -> None:
        # Mapping tên function -> tool object
        tool_map = {
            "make_file_txt": make_file_txt,
            "make_file_docx": make_file_docx,
            "make_invoice": make_invoice
        }

        if isinstance(ai_msg, AIMessage) and ai_msg.tool_calls:
            for call in ai_msg.tool_calls:
                tool_name = call["name"]
                tool_args = call["args"]

                print(f"🔧 Tool call: {tool_name} với args: {tool_args}")

                # Biến đổi kiểu dữ liệu của data_input nếu cần thiết
                # Đây là chuỗi dạng dict, không phải dict thật Dùng json.loads() lại bị lỗi vì:
                # JSON bắt buộc phải dùng " (double quote) → 'ngay' là không hợp lệ
                # Dẫn đến Pydantic báo lỗi ValidationError: data_input phải là dict
                # Vì nó có thể parse 'single-quoted dict' → dict
                # json.loads() chỉ dùng được với JSON chuẩn (double quotes, không comment)
 
                if isinstance(tool_args, dict) and "data_input" in tool_args and isinstance(tool_args["data_input"], str):
                    try:
                        tool_args["data_input"] = ast.literal_eval(tool_args["data_input"])
                    except Exception as e:
                        print(f"❌ Lỗi parse tool_args['data_input']: {e}")
                        continue
                    
                # Gọi tool nếu hợp lệ
                if tool_name in tool_map:
                    try:
                        tool_map[tool_name].invoke(tool_args)
                        
                        # Lưu lại vào memory sau khi gọi tool đánh dấu cho llm biết đã thực hiện tool call
                        memory.save_context(
                            {"input": "Yêu cầu"},
                            {"output": f"Đã chạy tool {tool_name} với args: {tool_args}, thoát khỏi chế độ tool call"}
                        )
                    except Exception as e:
                        print(f"Lỗi khi invoke tool {tool_name}: {e}")
                else:
                    print(f"Tool chưa định nghĩa: {tool_name}")

    def chat(self, message: str):
        # Tạo input context
        inputs = {
            "input": message,
            "history": self.memory.load_memory_variables({})["history"]
        }

        response = self.chain.invoke(inputs)

        # Lưu vào memory
        self.memory.save_context(
            {"input": message},
            {"output": response.content}
        )
        print("Câu hỏi: ", message)
        
        print("Trả lời: ", response.content)
        print("--" * 50)
        self.process_tool_calls(response, self.memory)
