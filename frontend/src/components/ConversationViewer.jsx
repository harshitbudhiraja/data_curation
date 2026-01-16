import { useState, useEffect } from 'react'
import axios from 'axios'
import { ChevronDown, Filter, Trash2, CheckCircle, XCircle } from 'lucide-react'
import ChatPanel from './ChatPanel'
import TestResults from './TestResults'

const API_BASE = 'http://localhost:8000'

export default function ConversationViewer() {
    const [dates, setDates] = useState([])
    const [personalities, setPersonalities] = useState([])
    const [conversations, setConversations] = useState([])
    const [selectedDate, setSelectedDate] = useState('')
    const [selectedPersonality, setSelectedPersonality] = useState('')
    const [selectedConversation, setSelectedConversation] = useState(null)
    const [showDiscarded, setShowDiscarded] = useState(false)
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(false)

    // Fetch dates on mount
    useEffect(() => {
        fetchDates()
    }, [])

    // Fetch personalities when date changes
    useEffect(() => {
        if (selectedDate) {
            fetchPersonalities(selectedDate)
        }
    }, [selectedDate])

    // Fetch conversations when personality changes
    useEffect(() => {
        if (selectedDate && selectedPersonality) {
            fetchConversations(selectedDate, selectedPersonality)
            fetchStats(selectedDate, selectedPersonality)
        }
    }, [selectedDate, selectedPersonality, showDiscarded])

    const fetchDates = async () => {
        try {
            const response = await axios.get(`${API_BASE}/api/dates`)
            setDates(response.data)
            if (response.data.length > 0) {
                setSelectedDate(response.data[0])
            }
        } catch (error) {
            console.error('Error fetching dates:', error)
        }
    }

    const fetchPersonalities = async (date) => {
        try {
            const response = await axios.get(`${API_BASE}/api/personalities/${date}`)
            setPersonalities(response.data)
            if (response.data.length > 0) {
                setSelectedPersonality(response.data[0])
            }
        } catch (error) {
            console.error('Error fetching personalities:', error)
        }
    }

    const fetchConversations = async (date, personality) => {
        setLoading(true)
        try {
            const response = await axios.get(
                `${API_BASE}/api/conversations/${date}/${personality}?include_discarded=${showDiscarded}`
            )
            setConversations(response.data)
            setSelectedConversation(null)
        } catch (error) {
            console.error('Error fetching conversations:', error)
        } finally {
            setLoading(false)
        }
    }

    const fetchStats = async (date, personality) => {
        try {
            const response = await axios.get(`${API_BASE}/api/stats/${date}/${personality}`)
            setStats(response.data)
        } catch (error) {
            console.error('Error fetching stats:', error)
        }
    }

    const fetchConversationDetails = async (id) => {
        try {
            const response = await axios.get(`${API_BASE}/api/conversation/${id}`)
            setSelectedConversation(response.data)
        } catch (error) {
            console.error('Error fetching conversation details:', error)
        }
    }

    const toggleDiscard = async (id) => {
        try {
            await axios.patch(`${API_BASE}/api/conversations/${id}/discard`)
            // Refresh conversations
            fetchConversations(selectedDate, selectedPersonality)
            if (selectedConversation?.id === id) {
                setSelectedConversation(null)
            }
        } catch (error) {
            console.error('Error toggling discard:', error)
        }
    }

    return (
        <div className="space-y-6">
            {/* Filters */}
            <div className="bg-white rounded-lg shadow p-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Date selector */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            📅 Date
                        </label>
                        <select
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            {dates.map((date) => (
                                <option key={date} value={date}>
                                    {date}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Personality selector */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            🎭 Personality
                        </label>
                        <select
                            value={selectedPersonality}
                            onChange={(e) => setSelectedPersonality(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            {personalities.map((personality) => (
                                <option key={personality} value={personality}>
                                    {personality.replace(/_/g, ' ')}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Show discarded toggle */}
                    <div className="flex items-end">
                        <label className="flex items-center space-x-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={showDiscarded}
                                onChange={(e) => setShowDiscarded(e.target.checked)}
                                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                            />
                            <span className="text-sm font-medium text-gray-700">
                                Show discarded
                            </span>
                        </label>
                    </div>
                </div>
            </div>

            {/* Stats */}
            {stats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-sm text-gray-600">Total</div>
                        <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-sm text-gray-600">Solved</div>
                        <div className="text-2xl font-bold text-green-600">{stats.solved}</div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-sm text-gray-600">Avg Turns</div>
                        <div className="text-2xl font-bold text-blue-600">{stats.avg_turns}</div>
                    </div>
                    <div className="bg-white rounded-lg shadow p-4">
                        <div className="text-sm text-gray-600">Tests Passed</div>
                        <div className="text-2xl font-bold text-purple-600">
                            {stats.total_tests_passed}/{stats.total_tests_possible}
                        </div>
                    </div>
                </div>
            )}

            {/* Conversation list and viewer */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                {/* Conversation list */}
                <div className="lg:col-span-1">
                    <div className="bg-white rounded-lg shadow">
                        <div className="p-4 border-b">
                            <h2 className="text-lg font-semibold text-gray-900">
                                Conversations ({conversations.length})
                            </h2>
                        </div>
                        <div className="divide-y max-h-[600px] overflow-y-auto">
                            {loading ? (
                                <div className="p-4 text-center text-gray-500">Loading...</div>
                            ) : conversations.length === 0 ? (
                                <div className="p-4 text-center text-gray-500">
                                    No conversations found
                                </div>
                            ) : (
                                conversations.map((conv) => (
                                    <div
                                        key={conv.id}
                                        onClick={() => fetchConversationDetails(conv.id)}
                                        className={`p-4 cursor-pointer hover:bg-gray-50 transition ${selectedConversation?.id === conv.id ? 'bg-blue-50' : ''
                                            }`}
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center space-x-2 mb-1">
                                                    <span className="text-sm font-medium text-gray-900">
                                                        Task {conv.task_id}
                                                    </span>
                                                    {conv.solved ? (
                                                        <CheckCircle className="w-4 h-4 text-green-500" />
                                                    ) : (
                                                        <XCircle className="w-4 h-4 text-red-500" />
                                                    )}
                                                </div>
                                                <p className="text-xs text-gray-600 line-clamp-2">
                                                    {conv.problem_text}
                                                </p>
                                                <div className="flex items-center space-x-3 mt-2 text-xs text-gray-500">
                                                    <span>🔄 {conv.turns} turns</span>
                                                    <span>
                                                        ✅ {conv.tests_passed}/{conv.total_tests}
                                                    </span>
                                                </div>
                                            </div>
                                            {conv.discarded && (
                                                <Trash2 className="w-4 h-4 text-gray-400 ml-2" />
                                            )}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                {/* Conversation viewer */}
                <div className="lg:col-span-4">
                    {selectedConversation ? (
                        <div className="space-y-4">
                            {/* Problem header */}
                            <div className="bg-white rounded-lg shadow p-4">
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex-1">
                                        <h3 className="text-lg font-semibold text-gray-900 mb-2">
                                            Problem {selectedConversation.task_id}
                                        </h3>
                                        <p className="text-gray-700">{selectedConversation.problem_text}</p>
                                    </div>
                                    <button
                                        onClick={() => toggleDiscard(selectedConversation.id)}
                                        className={`ml-4 px-4 py-2 rounded-md text-sm font-medium transition ${selectedConversation.discarded
                                                ? 'bg-green-100 text-green-700 hover:bg-green-200'
                                                : 'bg-red-100 text-red-700 hover:bg-red-200'
                                            }`}
                                    >
                                        {selectedConversation.discarded ? 'Restore' : 'Discard'}
                                    </button>
                                </div>

                                <div className="flex items-center space-x-4 text-sm">
                                    <span className={`px-2 py-1 rounded ${selectedConversation.solved
                                            ? 'bg-green-100 text-green-700'
                                            : 'bg-red-100 text-red-700'
                                        }`}>
                                        {selectedConversation.solved ? '✅ Solved' : '❌ Unsolved'}
                                    </span>
                                    <span className="text-gray-600">
                                        {selectedConversation.turns} turns
                                    </span>
                                    <span className="text-gray-600">
                                        {selectedConversation.tests_passed}/{selectedConversation.total_tests} tests passed
                                    </span>
                                </div>
                            </div>

                            {/* Chat panel */}
                            <ChatPanel conversation={selectedConversation.conversation} />

                            {/* Test results */}
                            {selectedConversation.execution_result && (
                                <TestResults
                                    result={selectedConversation.execution_result}
                                    testCases={selectedConversation.test_cases}
                                />
                            )}
                        </div>
                    ) : (
                        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
                            Select a conversation to view details
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
