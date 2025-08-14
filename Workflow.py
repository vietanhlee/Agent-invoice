from typing import TypedDict, List
from uuid import uuid4

from langgraph.graph import StateGraph, END, START
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash')
# Import your existing tools
from tools import (
    read_excel_data,
    get_prompt_for_data_excel,
    create_invoice_docx,
    InvoiceDetails,
)

# -------------------------
# 1. Khai báo AgentState
# -------------------------
class AgentState(TypedDict):
    user_request: str
    file_name: str
    raw_data: List[List[str]]
    extracted_data: InvoiceDetails
    final_docx: str
    response: str
    should_process_invoice: bool

# -------------------------
# 2. LLM Chat Node - Xử lý câu hỏi và trả lời
# -------------------------
def llm_chat_node(state: AgentState) -> AgentState:
    """Node LLM để chat và xử lý câu hỏi từ user."""
    print("💬 LLM đang xử lý câu hỏi...")
    
    user_question = state["user_request"]
    
    # Tạo prompt cho LLM
    chat_prompt = f"""
Bạn là một trợ lý AI thông minh chuyên về xử lý hóa đơn và kế toán.

Người dùng hỏi: "{user_question}"

Hãy phân tích câu hỏi và:
1. Nếu câu hỏi liên quan đến TẠO HÓA ĐƠN từ EXCEL, hãy trả lời: "PROCESS_INVOICE: [câu trả lời hướng dẫn]"
2. Nếu là câu hỏi thường, hãy trả lời trực tiếp một cách thân thiện và hữu ích.

Ví dụ:
- "Tạo hóa đơn từ Excel" → "PROCESS_INVOICE: Tôi sẽ giúp bạn tạo hóa đơn từ file Excel. Hãy cung cấp tên file Excel của bạn."
- "Hôm nay thế nào?" → "Tôi đang sẵn sàng hỗ trợ bạn! Bạn có cần giúp đỡ gì về hóa đơn không?"

Trả lời:
"""
    
    # Gọi LLM
    try:
        llm_response = llm.invoke(chat_prompt)
        response_content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
        
        # Kiểm tra xem có cần xử lý hóa đơn không
        if "PROCESS_INVOICE:" in response_content:
            state["should_process_invoice"] = True
            state["response"] = response_content.replace("PROCESS_INVOICE:", "").strip()
        else:
            state["should_process_invoice"] = False
            state["response"] = response_content
            
    except Exception as e:
        state["should_process_invoice"] = False
        state["response"] = f"Xin lỗi, có lỗi xảy ra: {str(e)}"
    
    return state

# -------------------------
# 3. Các node xử lý hóa đơn
# -------------------------
def read_excel_node(state: AgentState) -> AgentState:
    """Đọc dữ liệu từ Excel"""
    print("📥 Đọc dữ liệu từ Excel...")
    # try:
    state["raw_data"] = read_excel_data(file_path=state["file_name"])
    print(f"✅ Đã đọc {len(state['raw_data'])} dòng dữ liệu")
    # except Exception as e:
    #     print(f"❌ Lỗi đọc Excel: {e}")
    #     state["response"] = f"Lỗi khi đọc file Excel: {str(e)}"
    
    return state

def extract_info_node(state: AgentState) -> AgentState:
    """Trích xuất thông tin từ dữ liệu Excel"""
    print("🧠 Trích xuất thông tin từ dữ liệu Excel...")
    try:
        prompt = get_prompt_for_data_excel(data_excel_str=state["raw_data"])
        llm_response = llm.invoke(prompt)
        response_content = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)
        
        # TODO: Parse JSON response để tạo InvoiceDetails
        # Hiện tại chỉ lưu response string
        state["response"] = f"✅ Đã trích xuất thông tin: {response_content[:200]}..."
        
    except Exception as e:
        print(f"❌ Lỗi trích xuất: {e}")
        state["response"] = f"Lỗi khi trích xuất thông tin: {str(e)}"
    
    return state

def create_docx_node(state: AgentState) -> AgentState:
    """Tạo file hóa đơn DOCX"""
    print("📄 Tạo file hoá đơn DOCX...")
    try:
        if not state.get("final_docx"):
            state["final_docx"] = f"invoice_{uuid4().hex[:6]}.docx"

        output_path = create_invoice_docx(
            invoice_data=state["extracted_data"],
            output_path=state["final_docx"],
        )
        state["final_docx"] = output_path
        state["response"] = f"🎉 Đã tạo hóa đơn thành công tại: {output_path}"
        
    except Exception as e:
        print(f"❌ Lỗi tạo DOCX: {e}")
        state["response"] = f"Lỗi khi tạo file DOCX: {str(e)}"
    
    return state

# -------------------------
# 4. Function để định tuyến
# -------------------------
def determine_next_step(state: AgentState) -> str:
    """Xác định bước tiếp theo dựa trên state"""
    if state.get("should_process_invoice", False):
        print("🧭 Routing: Chuyển đến xử lý hóa đơn")
        return "read_excel"
    else:
        print("🧭 Routing: Chỉ chat, kết thúc")
        return "end"

# -------------------------
# 5. Xây dựng LangGraph
# -------------------------
def build_graph():
    """Xây dựng và trả về graph"""
    graph_builder = StateGraph(AgentState)

    # Thêm các nodes
    graph_builder.add_node(node= "llm_chat", action= llm_chat_node)
    graph_builder.add_node("read_excel", read_excel_node)
    graph_builder.add_node("extract_info", extract_info_node)
    graph_builder.add_node("create_docx", create_docx_node)

    # Set entry point
    graph_builder.set_entry_point("llm_chat")

    # Thêm conditional edges từ llm_chat
    graph_builder.add_conditional_edges(
        source= "llm_chat",
        path= determine_next_step,
        path_map= {
            "read_excel": "read_excel",
            "end": END,
        },
    )

    # Thêm các edges tuần tự cho quy trình xử lý hóa đơn
    graph_builder.add_edge(start_key="read_excel", end_key= "extract_info")
    graph_builder.add_edge("extract_info", "create_docx")
    graph_builder.add_edge("create_docx", END)

    return graph_builder.compile()

# Compile graph
app = build_graph()

# -------------------------
# 6. Interactive Chat Function
# -------------------------
def chat_with_agent():
    """Hàm chat tương tác với agent"""
    print("🤖 Chào mừng! Tôi có thể giúp gì cho bạn?")
    print("(Gõ 'quit' để thoát)")
    
    while True:
        user_input = input("\n👤 Bạn: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'thoát']:
            print("👋 Tạm biệt!")
            break
            
        if not user_input:
            continue
        
        try:
            # Tạo state cho câu hỏi
            initial_state = {
                "user_request": user_input,
                # "file_name": "test1.xlsx",  # Default file name
                # "raw_data": [],
                # "extracted_data": InvoiceDetails(
                #     ten_nguoi_ban="",
                #     dia_chi_nguoi_ban="",
                #     ten_nguoi_mua="",
                #     dia_chi_nguoi_mua="",
                #     ngay_hoa_don="",
                #     danh_sach_san_pham=[],
                #     tong_cong=0.0,
                #     thue_vat=0.0,
                #     tong_thanh_toan=0.0,
                # ),
                # "final_docx": "",
                # "response": "",
                # "should_process_invoice": False
            }
            
            # Chạy agent
            result = app.invoke(initial_state)
            
            # In response
            print(f"🤖 Agent: {result['response']}")
            
            # Nếu có tạo file thì thông báo
            if result.get('final_docx') and result['final_docx'] != "":
                print(f"📁 File đã tạo: {result['final_docx']}")
                
        except Exception as e:
            print(f"❌ Lỗi: {e}")

# -------------------------
# 7. Main execution
# -------------------------
if __name__ == "__main__":
    # # Test với sample data
    # sample_state = {
    #     "user_request": "Xin chào, bạn có thể giúp tôi tạo hóa đơn từ Excel không?",
    #     "file_name": "test1.xlsx",
    #     "raw_data": [],
    #     "extracted_data": InvoiceDetails(
    #         ten_nguoi_ban="Công ty ABC",
    #         dia_chi_nguoi_ban="Hà Nội",
    #         ten_nguoi_mua="Công ty XYZ",
    #         dia_chi_nguoi_mua="TP HCM",
    #         ngay_hoa_don="07/08/2025",
    #         danh_sach_san_pham=[],
    #         tong_cong=0.0,
    #         thue_vat=0.0,
    #         tong_thanh_toan=0.0,
    #     ),
    #     "final_docx": "",
    #     "response": "",
    #     "should_process_invoice": False
    # }

    # print("=== TEST RUN ===")
    # try:
    #     result = app.invoke(sample_state)
    #     print(f"✅ Response: {result['response']}")
    #     print(f"✅ Should process invoice: {result['should_process_invoice']}")
        
    #     if result.get('final_docx'):
    #         print(f"✅ File created: {result['final_docx']}")
            
    # except Exception as e:
    #     print(f"❌ Test failed: {e}")
    
    print("\n=== INTERACTIVE CHAT ===")
    chat_with_agent()