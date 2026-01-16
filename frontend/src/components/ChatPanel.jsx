import { User, Bot } from 'lucide-react'

export default function ChatPanel({ conversation }) {
    const renderCode = (content) => {
        // Check if content contains code
        const codeRegex = /```python\n([\s\S]*?)```|```\n([\s\S]*?)```/g
        const parts = []
        let lastIndex = 0
        let match

        while ((match = codeRegex.exec(content)) !== null) {
            // Add text before code
            if (match.index > lastIndex) {
                parts.push({
                    type: 'text',
                    content: content.slice(lastIndex, match.index),
                })
            }
            // Add code block
            parts.push({
                type: 'code',
                content: match[1] || match[2],
            })
            lastIndex = match.index + match[0].length
        }

        // Add remaining text
        if (lastIndex < content.length) {
            parts.push({
                type: 'text',
                content: content.slice(lastIndex),
            })
        }

        if (parts.length === 0) {
            parts.push({ type: 'text', content })
        }

        return parts.map((part, idx) =>
            part.type === 'code' ? (
                <pre key={idx} className="my-2 bg-gray-800 text-gray-100 p-3 rounded-lg text-xs whitespace-pre-wrap break-all max-w-full">
                    <code className="font-mono">{part.content}</code>
                </pre>
            ) : (
                <p key={idx} className="whitespace-pre-wrap break-words">
                    {part.content}
                </p>
            )
        )
    }

    return (
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            {/* Chat header */}
            <div className="bg-gradient-to-r from-blue-400 to-purple-400 px-6 py-4 text-white">
                <h3 className="text-lg font-semibold">Conversation</h3>
                <p className="text-sm text-blue-50">{conversation.length} messages</p>
            </div>

            {/* Chat messages - traditional vertical layout */}
            <div
                className="p-6 space-y-4 overflow-y-auto bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50"
                style={{ minHeight: '900px', maxHeight: '900px' }}
            >
                {conversation.map((msg, idx) => {
                    const isTutor = msg.role === 'tutor'
                    const hasExecution = msg.execution
                    
                    return (
                        <div
                            key={idx}
                            className={`flex ${isTutor ? 'justify-start' : 'justify-end'} animate-fade-in`}
                        >
                            <div className={`flex items-start space-x-3 max-w-[80%] ${isTutor ? 'flex-row' : 'flex-row-reverse space-x-reverse'}`}>
                                {/* Avatar */}
                                <div className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ${
                                    isTutor ? 'bg-emerald-200' : 'bg-blue-200'
                                }`}>
                                    {isTutor ? (
                                        <Bot className="w-5 h-5 text-emerald-700" />
                                    ) : (
                                        <User className="w-5 h-5 text-blue-700" />
                                    )}
                                </div>

                                {/* Message bubble */}
                                <div className="flex-1 min-w-0">
                                    <div className={`rounded-2xl px-4 py-3 ${
                                        isTutor
                                            ? 'bg-emerald-100 text-gray-800 border border-emerald-200 rounded-tl-sm'
                                            : 'bg-blue-100 text-gray-800 border border-blue-200 rounded-tr-sm'
                                    } shadow-sm`}>
                                        <div className="text-xs font-semibold mb-2 opacity-70 flex items-center justify-between">
                                            <span>{isTutor ? '👨‍🏫 Tutor' : '👨‍🎓 Student'} • Turn {msg.turn}</span>
                                            {hasExecution && (
                                                <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-bold ${
                                                    hasExecution.success 
                                                        ? 'bg-green-200 text-green-800' 
                                                        : 'bg-red-200 text-red-800'
                                                }`}>
                                                    {hasExecution.success ? '✅' : '❌'} {hasExecution.tests_passed}/{hasExecution.total_tests} tests
                                                </span>
                                            )}
                                        </div>
                                        <div className="text-sm leading-relaxed break-words">
                                            {renderCode(msg.content)}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
