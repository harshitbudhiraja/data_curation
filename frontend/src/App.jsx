import './index.css'
import ConversationViewer from './components/ConversationViewer'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50">
      <header className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 shadow-xl">
        <div className="w-full px-6 py-5">
          <h1 className="text-3xl font-bold text-white tracking-tight text-center">
            Conversation Viewer
          </h1>
        </div>
      </header>

      <main className="max-w-[95%] mx-auto px-6 py-8">
        <ConversationViewer />
      </main>
    </div>
  )
}

export default App
