import { useState } from 'react'
import './index.css'
import ConversationViewer from './components/ConversationViewer'
import CodingQuestionsViewer from './components/CodingQuestionsViewer'

function App() {
  const [activeTab, setActiveTab] = useState('conversations')

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50">
      <header className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 shadow-xl">
        <div className="w-full px-6 py-5">
          <h1 className="text-3xl font-bold text-white tracking-tight text-center mb-4">
            Dataset Viewer
          </h1>
          
          {/* Tabs */}
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => setActiveTab('conversations')}
              className={`px-6 py-2.5 rounded-lg font-medium transition-all ${
                activeTab === 'conversations'
                  ? 'bg-white text-purple-600 shadow-lg'
                  : 'bg-purple-500/30 text-white hover:bg-purple-500/50'
              }`}
            >
              Conversations
            </button>
            <button
              onClick={() => setActiveTab('coding-questions')}
              className={`px-6 py-2.5 rounded-lg font-medium transition-all ${
                activeTab === 'coding-questions'
                  ? 'bg-white text-purple-600 shadow-lg'
                  : 'bg-purple-500/30 text-white hover:bg-purple-500/50'
              }`}
            >
              Coding Questions
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-[95%] mx-auto px-6 py-8">
        {activeTab === 'conversations' ? (
          <ConversationViewer />
        ) : (
          <CodingQuestionsViewer />
        )}
      </main>
    </div>
  )
}

export default App
