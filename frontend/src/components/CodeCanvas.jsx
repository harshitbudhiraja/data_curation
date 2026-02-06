import { useState } from 'react'
import { Code2, Play, ToggleLeft, ToggleRight } from 'lucide-react'

export default function CodeCanvas({ code, execution, turn, autoSync, onToggleSync }) {
    return (
        <div className="sticky top-4 h-[calc(100vh-120px)] flex flex-col bg-white rounded-lg shadow-lg overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-gray-800 to-gray-900 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center space-x-2 text-white">
                    <Code2 className="w-5 h-5" />
                    <span className="font-semibold">Code Canvas</span>
                    {turn && (
                        <span className="text-xs bg-white/20 px-2 py-1 rounded">
                            Turn {turn}
                        </span>
                    )}
                </div>
                
                {/* Auto-sync toggle */}
                <button
                    onClick={onToggleSync}
                    className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-sm font-medium transition ${
                        autoSync 
                            ? 'bg-blue-500 text-white hover:bg-blue-600' 
                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                    title={autoSync ? 'Auto-sync enabled' : 'Auto-sync disabled'}
                >
                    {autoSync ? (
                        <>
                            <ToggleRight className="w-4 h-4" />
                            <span>Sync</span>
                        </>
                    ) : (
                        <>
                            <ToggleLeft className="w-4 h-4" />
                            <span>Manual</span>
                        </>
                    )}
                </button>
            </div>

            {/* Code editor */}
            <div className="flex-1 overflow-auto bg-gray-900">
                {code ? (
                    <pre className="p-4 text-sm text-gray-100 font-mono leading-relaxed">
                        <code>{code}</code>
                    </pre>
                ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">
                        <div className="text-center">
                            <Code2 className="w-12 h-12 mx-auto mb-3 opacity-50" />
                            <p className="text-sm">No code to display</p>
                            <p className="text-xs mt-1">Scroll through the conversation to see code</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Execution results */}
            {execution && (
                <div className={`border-t-2 p-4 ${
                    execution.success 
                        ? 'bg-green-50 border-green-500' 
                        : 'bg-red-50 border-red-500'
                }`}>
                    <div className="flex items-center space-x-2 mb-2">
                        <Play className={`w-4 h-4 ${
                            execution.success ? 'text-green-600' : 'text-red-600'
                        }`} />
                        <span className={`font-semibold text-sm ${
                            execution.success ? 'text-green-800' : 'text-red-800'
                        }`}>
                            Execution Result
                        </span>
                    </div>
                    
                    <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-700">Tests Passed:</span>
                            <span className={`font-bold ${
                                execution.success ? 'text-green-700' : 'text-red-700'
                            }`}>
                                {execution.tests_passed}/{execution.total_tests}
                            </span>
                        </div>
                        
                        {!execution.success && execution.message && (
                            <div className="mt-2 p-2 bg-white rounded border border-red-200">
                                <p className="text-xs font-semibold text-red-800 mb-1">Error:</p>
                                <p className="text-xs text-red-700 font-mono break-words">
                                    {execution.message}
                                </p>
                            </div>
                        )}
                        
                        {execution.success && (
                            <div className="mt-2 p-2 bg-white rounded border border-green-200">
                                <p className="text-xs text-green-700 font-semibold">
                                    ✅ All tests passed successfully!
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}
