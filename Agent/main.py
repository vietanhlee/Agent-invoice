from ChatBotAgent import ChatBot

prompt_hoa_don = '''ngày 12 thang 7 nam 2025 kí hiệu là HD001 tên người bán : Lê Việt Anh mã số thuế người bán: 123456789 địa chỉ bán là: Hà Nội, điện thoại người bán: 0123456789, số tài khoản người bán: 12345678, tên người mua: Nguyễn Văn B, mã số thuế người mua: 987654321, địa chỉ người mua: TP.HCM, số điện thoại người mua: 0987654321, số tài khoản người mua: 87654321, hình thức thanh toán: Chuyển khoản'''
chat_bot = ChatBot()

while True:
    mes = input('Nhập nội dung: ')
    if mes.lower() == 'ẽit':
        break
    
    print()
    res = chat_bot.chat(message= mes)
    print(f'chatbot: {res['messages'][-1].content}')
    print()
    print('-' * 100)
    print()




# xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx 
# Agent khác Workflow rất nhiều nó có thể tự chọn các tool cho đến khi ra kết quả cuối cùng còn workflow
# thì tự setup các node và các định tuyến router. Agent có thể tự chọn các tool cho đến khi ra kết quả. Nhưng
# trong llm vẫn cần có promt để hướng dẫn nó quy trình thực hiện việc gì đó. ví dụ việc A = x + y + z, B = x + y thì 
# cũng phải viết vào prompt để hướng dẫn Agent hoạt động. Mặc dù các tool có docstring rõ ràng nhưng nếu nghiệp vụ quá 
# chuyên sâu thì Agent không thể kết hợp các tool lại để dùng mà ra kết quả được. Nói chung phải có prompt hướng dẫn rõ ràng