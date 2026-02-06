import { useState, useEffect } from 'react'
import axios from 'axios'
import { ChevronLeft, ChevronRight, BookOpen } from 'lucide-react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

const API_BASE = 'http://localhost:8000'
const ITEMS_PER_PAGE = 20

export default function CodingQuestionsViewer() {
    const [questions, setQuestions] = useState([])
    const [selectedQuestion, setSelectedQuestion] = useState(null)
    const [loading, setLoading] = useState(false)
    const [currentPage, setCurrentPage] = useState(1)
    const [totalPages, setTotalPages] = useState(0)

    useEffect(() => {
        fetchQuestions()
    }, [])

    useEffect(() => {
        if (questions.length > 0) {
            setTotalPages(Math.ceil(questions.length / ITEMS_PER_PAGE))
        }
    }, [questions])

    const fetchQuestions = async () => {
        setLoading(true)
        try {
            const response = await axios.get(`${API_BASE}/api/coding-questions`)
            setQuestions(response.data)
        } catch (error) {
            console.error('Error fetching coding questions:', error)
        } finally {
            setLoading(false)
        }
    }

    const getCurrentPageQuestions = () => {
        const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
        const endIndex = startIndex + ITEMS_PER_PAGE
        return questions.slice(startIndex, endIndex)
    }

    const handleNextPage = () => {
        if (currentPage < totalPages) {
            setCurrentPage(currentPage + 1)
        }
    }

    const handlePrevPage = () => {
        if (currentPage > 1) {
            setCurrentPage(currentPage - 1)
        }
    }

    const getDifficultyColor = (difficulty) => {
        switch (difficulty?.toLowerCase()) {
            case 'easy':
                return 'bg-green-100 text-green-700'
            case 'medium':
                return 'bg-yellow-100 text-yellow-700'
            case 'difficult':
                return 'bg-red-100 text-red-700'
            default:
                return 'bg-gray-100 text-gray-700'
        }
    }

    const getSourceColor = (source) => {
        switch (source) {
            case 'MBPP':
                return 'bg-blue-100 text-blue-700'
            case 'HumanEval':
                return 'bg-purple-100 text-purple-700'
            default:
                return 'bg-gray-100 text-gray-700'
        }
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <BookOpen className="w-6 h-6 text-purple-600" />
                        <h2 className="text-xl font-semibold text-gray-900">Coding Questions</h2>
                    </div>
                    <div className="text-sm text-gray-600">
                        Total: {questions.length} questions
                    </div>
                </div>
            </div>

            {/* Main content */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                {/* Question list */}
                <div className="lg:col-span-2">
                    <div className="bg-white rounded-lg shadow">
                        <div className="p-4 border-b">
                            <h3 className="text-lg font-semibold text-gray-900">
                                Questions {(currentPage - 1) * ITEMS_PER_PAGE + 1} - {Math.min(currentPage * ITEMS_PER_PAGE, questions.length)}
                            </h3>
                        </div>
                        <div className="divide-y max-h-[600px] overflow-y-auto">
                            {loading ? (
                                <div className="p-4 text-center text-gray-500">Loading...</div>
                            ) : getCurrentPageQuestions().length === 0 ? (
                                <div className="p-4 text-center text-gray-500">
                                    No questions found
                                </div>
                            ) : (
                                getCurrentPageQuestions().map((question) => (
                                    <div
                                        key={question.task_id}
                                        onClick={() => setSelectedQuestion(question)}
                                        className={`p-4 cursor-pointer hover:bg-gray-50 transition border-l-4 ${
                                            selectedQuestion?.task_id === question.task_id 
                                                ? 'bg-blue-50 border-blue-500' 
                                                : 'border-transparent'
                                        }`}
                                    >
                                        <div className="space-y-2">
                                            <div className="flex items-center space-x-2">
                                                <span className="text-sm font-bold text-blue-600">
                                                    #{question.task_id}
                                                </span>
                                                <span className={`px-2 py-0.5 rounded text-xs font-medium ${getSourceColor(question.source)}`}>
                                                    {question.source}
                                                </span>
                                                <span className={`px-2 py-0.5 rounded text-xs font-medium ${getDifficultyColor(question.difficulty)}`}>
                                                    {question.difficulty}
                                                </span>
                                            </div>
                                            <p className="text-sm text-gray-700 line-clamp-2">
                                                {question.text}
                                            </p>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                        
                        {/* Pagination */}
                        <div className="p-4 border-t flex items-center justify-between">
                            <button
                                onClick={handlePrevPage}
                                disabled={currentPage === 1}
                                className="flex items-center space-x-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <ChevronLeft className="w-4 h-4" />
                                <span>Previous</span>
                            </button>
                            
                            <span className="text-sm text-gray-600">
                                Page {currentPage} of {totalPages}
                            </span>
                            
                            <button
                                onClick={handleNextPage}
                                disabled={currentPage === totalPages}
                                className="flex items-center space-x-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <span>Next</span>
                                <ChevronRight className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Question details */}
                <div className="lg:col-span-3">
                    {selectedQuestion ? (
                        <div className="bg-white rounded-lg shadow max-h-[700px] overflow-y-auto">
                            <div className="p-6 space-y-6">
                                {/* Header */}
                                <div>
                                    <div className="flex items-center flex-wrap gap-2 mb-3">
                                        <span className="text-sm font-semibold text-gray-700">
                                            Task #{selectedQuestion.task_id}
                                        </span>
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${getSourceColor(selectedQuestion.source)}`}>
                                            {selectedQuestion.source}
                                        </span>
                                        {selectedQuestion.source_task_id && (
                                            <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-700">
                                                {selectedQuestion.source_task_id}
                                            </span>
                                        )}
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${getDifficultyColor(selectedQuestion.difficulty)}`}>
                                            {selectedQuestion.difficulty}
                                        </span>
                                    </div>
                                    <p className="text-gray-900 font-medium leading-relaxed mb-4">
                                        {selectedQuestion.text}
                                    </p>
                                </div>

                                {/* Solution Code */}
                                <div>
                                    <div className="flex items-center space-x-2 mb-3">
                                        <span className="text-sm font-semibold text-gray-700">
                                            ✓ Solution Code
                                        </span>
                                    </div>
                                    <div className="rounded-lg overflow-hidden">
                                        <SyntaxHighlighter
                                            language="python"
                                            style={vscDarkPlus}
                                            customStyle={{
                                                margin: 0,
                                                borderRadius: '0.5rem',
                                                fontSize: '0.875rem'
                                            }}
                                        >
                                            {selectedQuestion.code}
                                        </SyntaxHighlighter>
                                    </div>
                                </div>

                                {/* Test Cases */}
                                <div>
                                    <h4 className="text-sm font-semibold text-gray-700 mb-3">
                                        Test Cases
                                    </h4>
                                    <div className="space-y-2">
                                        {selectedQuestion.test_list.map((test, index) => (
                                            <div
                                                key={index}
                                                className="bg-gray-50 rounded-lg p-3 font-mono text-sm text-gray-800 border border-gray-200"
                                            >
                                                {test}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="bg-white rounded-lg shadow p-12 text-center">
                            <BookOpen className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                            <p className="text-gray-500 text-lg">
                                Select a question to view details
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
