<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot Tư Vấn Sản Phẩm</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100..900;1,100..900&display=swap"
        rel="stylesheet">

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/showdown/2.1.0/showdown.min.js"></script>
    <style>
        body {
            font-family: "Roboto", sans-serif;
            margin: 0;
            padding: 0;
            height: 100vh;
            background-color: #f0f2f5;
            /* Background chung cho trang */
        }

        /* Lottie Icon Styling */
        .lottie-chat-icon {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 100px;
            /* Kích thước icon Lottie */
            height: 100px;
            cursor: pointer;
            z-index: 1000;

            transition: transform 0.3s ease;
        }

        .lottie-chat-icon:hover {
            transform: scale(1.1);
        }

        /* Chatbox Styling */
        .chatbot-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 350px;
            height: 500px;
            background-color: #ffffff;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            z-index: 999;
            transform: translateY(20px) scale(0.9);
            opacity: 0;
            visibility: hidden;
            transition: all 0.4s cubic-bezier(0.68, -0.55, 0.27, 1.55);
            /* Hiệu ứng pop-out */
        }

        .chatbot-container.active {
            transform: translateY(0) scale(1);
            opacity: 1;
            visibility: visible;
        }

        .chatbot-header {
            background-color: #ffc91b;
            /* Màu header chatbot */
            color: white;
            padding: 10px;
            border-top-left-radius: 15px;
            border-top-right-radius: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chatbot-header p {
            color: black;
            font-size: 1rem;
            font-weight: bold;
        }

        .chatbot-header .close-btn {
            background: none;
            border: none;
            color: black;
            font-size: 1.5rem;
            cursor: pointer;
            opacity: 0.8;
            transition: opacity 0.3s ease;
        }

        .chatbot-header .close-btn:hover {
            opacity: 1;
        }

        .chatbot-body {
            flex-grow: 1;
            padding: 15px;
            overflow-y: auto;
            background-color: #f8f9fa;
            /* Màu nền body chat */
            display: flex;
            flex-direction: column;
        }

        .chatbot-body::-webkit-scrollbar {
            width: 8px;
        }

        .chatbot-body::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }

        .chatbot-body::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 10px;
        }

        .chatbot-body::-webkit-scrollbar-thumb:hover {
            background: #555;
        }

        .chatbot-footer {
            padding: 15px;
            border-top: 1px solid #e9ecef;
            display: flex;
            align-items: center;
            background-color: #ffffff;
            border-bottom-left-radius: 15px;
            border-bottom-right-radius: 15px;
        }

        .chatbot-footer .form-control {
            border-radius: 20px;
            padding: 10px 15px;
            border: 1px solid #ced4da;
            resize: none;
            /* Không cho phép thay đổi kích thước input */
            box-shadow: none;
        }

        .chatbot-footer .btn {
            border-radius: 20px;
            margin-left: 10px;
            padding: 10px 15px;
        }

        /* New styling for input with send icon */
        .message-input-wrapper {
            position: relative;
            flex-grow: 1;
            display: flex;
            /* Để icon và textarea nằm trên cùng một dòng và căn chỉnh dễ hơn */
            align-items: center;
        }

        .chatbot-footer .form-control {
            flex-grow: 1;
            padding-right: 45px;
            /* Để tạo không gian cho icon */
        }

        .send-icon {
            position: absolute;
            right: 10px;
            /* Điều chỉnh vị trí của icon */
            width: 28px;
            /* Kích thước icon */
            height: 28px;
            cursor: pointer;
            transition: transform 0.2s ease;
        }

        .send-icon:hover {
            transform: scale(1.1);
        }

        /* Message Styling */
        .message {
            max-width: 85%;
            /* Tăng max-width để chứa bảng */
            padding: 8px 12px;
            border-radius: 12px;
            margin-bottom: 10px;
            word-wrap: break-word;
        }

        .message.user {
            background-color: #007bff;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }

        .message.bot {
            background-color: #e2e6ea;
            color: #333;
            align-self: flex-start;
            border-bottom-left-radius: 2px;
        }

        /* *** CSS CHO BẢNG MARKDOWN CỦA BOT ***
        */
        .message.bot table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 5px;
            margin-bottom: 5px;
            background-color: #ffffff;
            font-size: 0.9em;
        }

        .message.bot th,
        .message.bot td {
            border: 1px solid #dee2e6;
            padding: 6px 10px;
            text-align: left;
        }

        .message.bot th {
            background-color: #f1f1f1;
        }

        /* *** HẾT PHẦN CSS BẢNG ***
        */

        /* Typing Indicator Styling */
        .typing-indicator {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-top: 10px;
            font-size: 1.2em;
            color: #555;
        }

        .typing-indicator span {
            animation: blink 1.4s infinite ease-in-out;
        }

        .typing-indicator span:nth-child(1) {
            animation-delay: -0.32s;
        }

        .typing-indicator span:nth-child(2) {
            animation-delay: -0.16s;
        }

        .typing-indicator span:nth-child(3) {
            animation-delay: 0s;
        }

        @keyframes blink {

            0%,
            80%,
            100% {
                opacity: 0;
            }

            40% {
                opacity: 1;
            }
        }
    </style>
</head>

<body>

    <div id="lottieIcon" class="lottie-chat-icon">
        <lottie-player src="ChatLoading.json" background="transparent" speed="1"
            style="width: 100%; height: 100%;" loop autoplay></lottie-player>
    </div>

    <div id="chatbotContainer" class="chatbot-container">
        <div class="chatbot-header">
            <p class="mb-0">Chat Bot tư vấn khách hàng</p>
            <button type="button" class="close-btn" id="closeChatbot">
                &times;
            </button>
        </div>
        <div class="chatbot-body" id="chatboxBody">
            <div class="message bot">Chào bạn! Tôi có thể giúp gì cho bạn?</div>
        </div>
        <div class="chatbot-footer">
            <div class="message-input-wrapper">
                <input type="text" id="messageInput" class="form-control" placeholder="Nhập tin nhắn..."
                    rows="1"></input>
                <img src="send.png" alt="Send" id="sendIcon" class="send-icon">
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

    <script>
        // -----------------------------------------------------------------
        // *** KHU VỰC CẤU HÌNH ***
        // -----------------------------------------------------------------

        // KHI TEST LOCAL (chạy python main.py)
        const API_BASE_URL = 'http://127.0.0.1:8000';

        // KHI DEPLOY LÊN RAILWAY (Lấy URL từ Dashboard Railway)
        // const API_BASE_URL = 'https://your-backend-app-name.up.railway.app';

        // -----------------------------------------------------------------
        // *** BƯỚC 1: THÊM BIẾN LỊCH SỬ CHAT ***
        // -----------------------------------------------------------------
        let chatHistory = [];
        const MAX_HISTORY_TURNS = 3; // Chỉ nhớ 3 lượt chat cuối (6 tin nhắn)
        // -----------------------------------------------------------------

        const lottieIcon = document.getElementById('lottieIcon');
        const chatbotContainer = document.getElementById('chatbotContainer');
        const closeChatbotBtn = document.getElementById('closeChatbot');
        const messageInput = document.getElementById('messageInput');
        const sendIcon = document.getElementById('sendIcon');
        const chatboxBody = document.getElementById('chatboxBody');

        // Khởi tạo trình chuyển đổi Markdown (Showdown)
        const markdownConverter = new showdown.Converter({
            tables: true,
            simpleLineBreaks: true
        });

        lottieIcon.addEventListener('click', () => {
            chatbotContainer.classList.toggle('active');
            lottieIcon.style.display = 'none';
        });

        closeChatbotBtn.addEventListener('click', () => {
            chatbotContainer.classList.remove('active');
            lottieIcon.style.display = 'block';
        });

        // (Hàm addMessage giữ nguyên)
        function addMessage(text, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', sender);
            if (sender === 'bot') {
                const html = markdownConverter.makeHtml(text);
                messageDiv.innerHTML = html;
            } else {
                messageDiv.textContent = text;
            }
            chatboxBody.appendChild(messageDiv);
            chatboxBody.scrollTop = chatboxBody.scrollHeight;
            return messageDiv;
        }

        // -----------------------------------------------------------------
        // *** BƯỚC 2: CẬP NHẬT HÀM GỬI TIN NHẮN ***
        // -----------------------------------------------------------------
        async function sendMessage() {
            const messageText = messageInput.value.trim();
            if (messageText) {
                addMessage(messageText, 'user');
                messageInput.value = '';

                // Hiển thị "typing..."
                const typingIndicatorDiv = document.createElement('div');
                typingIndicatorDiv.classList.add('message', 'bot', 'typing-indicator');
                typingIndicatorDiv.innerHTML = '<span>.</span><span>.</span><span>.</span>';
                chatboxBody.appendChild(typingIndicatorDiv);
                chatboxBody.scrollTop = chatboxBody.scrollHeight;

                try {
                    const response = await fetch(
                        `${API_BASE_URL}/api/chat`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                query: messageText,
                                history: chatHistory // <-- GỬI LỊCH SỬ LÊN
                            }),
                        });

                    if (typingIndicatorDiv.parentNode) {
                        typingIndicatorDiv.parentNode.removeChild(typingIndicatorDiv);
                    }

                    const data = await response.json();
                    if (response.ok) {
                        const botAnswer = data.answer;
                        addMessage(botAnswer, 'bot');

                        // *** BƯỚC 3: CẬP NHẬT LỊCH SỬ CHAT ***
                        chatHistory.push({
                            "role": "user",
                            "content": messageText
                        });
                        chatHistory.push({
                            "role": "bot",
                            "content": botAnswer
                        });

                        // Giới hạn lịch sử (chỉ giữ 3 lượt cuối)
                        if (chatHistory.length > MAX_HISTORY_TURNS * 2) {
                            chatHistory = chatHistory.slice(-MAX_HISTORY_TURNS * 2);
                        }

                    } else {
                        addMessage(`Lỗi: ${data.detail || 'Không thể kết nối đến chatbot.'}`, 'bot');
                    }
                } catch (error) {
                    console.error('Lỗi khi gọi API:', error);
                    if (typingIndicatorDiv.parentNode) {
                        typingIndicatorDiv.parentNode.removeChild(typingIndicatorDiv);
                    }
                    addMessage(
                        'Rất tiếc, có lỗi xảy ra khi kết nối đến chatbot. Vui lòng thử lại sau.',
                        'bot');
                }
            }
        }
        // --- HẾT PHẦN SỬA LỖI ---

        // Gắn sự kiện click cho icon gửi
        sendIcon.addEventListener('click', sendMessage);

        // Gắn sự kiện Enter cho ô input
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    </script>

</body>

</html>