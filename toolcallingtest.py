from langchain.memory import ConversationBufferMemory
from langchain.prompts import  (ChatPromptTemplate,
                                SystemMessagePromptTemplate,
                                HumanMessagePromptTemplate,
                                MessagesPlaceholder)
from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
import ast
from tools import make_file_txt, make_file_docx, make_invoice

system_promt = "Bạn là một trợ lý ảo thông minh. Bạn có thể tạo file .txt và .docx với nội dung được người dùng cung cấp."
class ChatBot:
    def __init__(self):
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
        self.llm_with_tools = llm.bind_tools([make_file_txt, make_file_docx, make_invoice])

        self.memory = ConversationBufferMemory(memory_key= "history", return_messages=True)

        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                system_promt
            ),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}")
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
                        # invoke chạy tool tương ứng với tham số tool_args tương ứng
                        tool_map[tool_name].invoke(tool_args)
                        
                        # Lưu lại vào memory sau khi gọi tool đánh dấu cho llm biết đã thực hiện tool call
                        memory.save_context(
                            {"input": "Yêu cầu"},
                            {"output": f"Đã chạy tool {tool_name} với args: {tool_args}, thoát khỏi chế độ tool call"}
                        )
                    except Exception as e:
                        memory.save_context(
                            {"input": "Yêu cầu"},
                            {"output": f"Yêu cầu chạy {tool_name} với args: {tool_args} chưa được thực hiện do lỗi: {e}"}
                        )
                else:
                    print(f"Tool chưa định nghĩa: {tool_name}")

    def chat(self, message: str):
        # Tạo input context
        inputs = {
            "input": message,
            "history": self.memory.load_memory_variables({})["history"]
        }

        response = self.chain.invoke(input= inputs)

        # Lưu vào memory
        self.memory.save_context(
            inputs= {"input": message},
            outputs= {"output": response.content}
        )
        self.process_tool_calls(response, self.memory)
        return response.content 


# --- Tạo đối tượng ChatLLM --- for testing
chat_llm = ChatBot()
while True:
    user_input = input("Bạn: ")
    if user_input.lower() in ["exit", "quit", "bye"]:
        print("Kết thúc cuộc trò chuyện. Tạm biệt!")
        break
    response = chat_llm.chat(user_input)
    print("AI:", response)
    # print("\n--- Lịch sử trò chuyện đã được cập nhật ---")
    # print(chat_llm.memory.buffer)
    print("-" * 100)