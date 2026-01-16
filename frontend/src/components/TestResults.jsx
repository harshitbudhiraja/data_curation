import { CheckCircle, XCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

export default function TestResults({ result, testCases }) {
    const [expanded, setExpanded] = useState(false)

    const success = result.success
    const testsPassed = result.tests_passed || 0
    const totalTests = testCases.length
    const progressPercent = totalTests > 0 ? (testsPassed / totalTests) * 100 : 0

    return (
        <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="p-4 border-b">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">Test Results</h3>
                    <div className="flex items-center space-x-2">
                        {success ? (
                            <span className="flex items-center space-x-1 text-green-600">
                                <CheckCircle className="w-5 h-5" />
                                <span className="font-medium">All tests passed</span>
                            </span>
                        ) : (
                            <span className="flex items-center space-x-1 text-red-600">
                                <XCircle className="w-5 h-5" />
                                <span className="font-medium">Tests failed</span>
                            </span>
                        )}
                    </div>
                </div>

                {/* Progress bar */}
                <div className="mb-3">
                    <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                        <span>Tests Passed</span>
                        <span className="font-medium">
                            {testsPassed}/{totalTests}
                        </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                            className={`h-2 rounded-full transition-all ${success ? 'bg-green-500' : 'bg-red-500'
                                }`}
                            style={{ width: `${progressPercent}%` }}
                        />
                    </div>
                </div>

                {/* Error message */}
                {!success && result.message && (
                    <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-3">
                        <p className="text-sm text-red-800">
                            <span className="font-medium">Error:</span> {result.message}
                        </p>
                    </div>
                )}

                {/* Toggle details button */}
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                    {expanded ? (
                        <>
                            <ChevronUp className="w-4 h-4" />
                            <span>Hide details</span>
                        </>
                    ) : (
                        <>
                            <ChevronDown className="w-4 h-4" />
                            <span>Show details</span>
                        </>
                    )}
                </button>
            </div>

            {/* Expanded details */}
            {expanded && (
                <div className="p-4 space-y-4">
                    {/* Test cases */}
                    <div>
                        <h4 className="text-sm font-semibold text-gray-900 mb-2">Test Cases</h4>
                        <div className="space-y-2">
                            {testCases.map((test, idx) => (
                                <div
                                    key={idx}
                                    className="bg-gray-50 rounded-md p-3 border border-gray-200"
                                >
                                    <code className="text-xs text-gray-800">{test}</code>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Code output */}
                    {result.code_output && (
                        <div>
                            <h4 className="text-sm font-semibold text-gray-900 mb-2">Code Output</h4>
                            <pre className="bg-gray-900 text-gray-100 rounded-md p-3 text-xs overflow-x-auto">
                                {result.code_output}
                            </pre>
                        </div>
                    )}

                    {/* Test output */}
                    {result.test_results && (
                        <div>
                            <h4 className="text-sm font-semibold text-gray-900 mb-2">Test Output</h4>
                            <pre className="bg-gray-900 text-gray-100 rounded-md p-3 text-xs overflow-x-auto">
                                {result.test_results}
                            </pre>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
