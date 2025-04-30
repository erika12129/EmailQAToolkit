const { useState } = React;

function App() {
    const [emailFile, setEmailFile] = useState(null);
    const [reqFile, setReqFile] = useState(null);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleFileChange = (e, setFile) => {
        setFile(e.target.files[0]);
        setError(null);
    };

    const handleDrop = (e, setFile) => {
        e.preventDefault();
        setFile(e.dataTransfer.files[0]);
        setError(null);
    };

    const handleDragOver = (e) => e.preventDefault();

    const runQA = async () => {
        if (!emailFile || !reqFile) {
            setError("Please upload both email HTML and requirements JSON files.");
            return;
        }
        setLoading(true);
        setError(null);
        setResults(null);

        const formData = new FormData();
        formData.append("email", emailFile);
        formData.append("requirements", reqFile);

        try {
            // Use relative URL for API endpoint - works when served by same server
            const response = await fetch("/run-qa", {
                method: "POST",
                body: formData,
            });
            const data = await response.json();
            if (response.ok) {
                setResults(data);
            } else {
                setError(data.detail || "Failed to process QA.");
            }
        } catch (err) {
            setError("Error connecting to server: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 p-6">
            <div className="max-w-4xl mx-auto bg-white shadow-lg rounded-lg p-8">
                <h1 className="text-2xl font-bold mb-6 text-center">Email QA Automation</h1>

                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Upload Email HTML
                    </label>
                    <div
                        className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center"
                        onDrop={(e) => handleDrop(e, setEmailFile)}
                        onDragOver={handleDragOver}
                    >
                        <input
                            type="file"
                            accept=".html"
                            onChange={(e) => handleFileChange(e, setEmailFile)}
                            className="hidden"
                            id="email-upload"
                        />
                        <label htmlFor="email-upload" className="cursor-pointer text-blue-600 hover:underline">
                            {emailFile ? emailFile.name : "Drag or click to upload email HTML"}
                        </label>
                    </div>
                </div>

                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                        Upload Requirements JSON
                    </label>
                    <div
                        className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center"
                        onDrop={(e) => handleDrop(e, setReqFile)}
                        onDragOver={handleDragOver}
                    >
                        <input
                            type="file"
                            accept=".json"
                            onChange={(e) => handleFileChange(e, setReqFile)}
                            className="hidden"
                            id="req-upload"
                        />
                        <label htmlFor="req-upload" className="cursor-pointer text-blue-600 hover:underline">
                            {reqFile ? reqFile.name : "Drag or click to upload requirements JSON"}
                        </label>
                    </div>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-100 text-red-700 rounded-lg">
                        {error}
                    </div>
                )}

                <button
                    onClick={runQA}
                    disabled={loading}
                    className={`w-full py-2 px-4 rounded-lg text-white font-semibold ${
                        loading ? "bg-gray-400 cursor-not-allowed" : "bg-blue-600 hover:bg-blue-700"
                    }`}
                >
                    {loading ? "Running QA..." : "Run QA"}
                </button>

                {results && (
                    <div className="mt-8">
                        <h2 className="text-xl font-semibold mb-4">QA Results</h2>
                        <div className="space-y-6">
                            <div>
                                <h3 className="text-lg font-medium mb-2">Metadata</h3>
                                <div className="overflow-x-auto">
                                    <table className="w-full border-collapse">
                                        <thead>
                                            <tr className="bg-gray-200">
                                                <th className="border p-2">Field</th>
                                                <th className="border p-2">Expected</th>
                                                <th className="border p-2">Actual</th>
                                                <th className="border p-2">Status</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {results.metadata.map((item, index) => (
                                                <tr key={index} className="border">
                                                    <td className="border p-2">{item.field}</td>
                                                    <td className="border p-2">{item.expected}</td>
                                                    <td className="border p-2">{item.actual}</td>
                                                    <td
                                                        className={`border p-2 ${
                                                            item.status === "PASS"
                                                                ? "text-green-600"
                                                                : "text-red-600"
                                                        }`}
                                                    >
                                                        {item.status}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                            <div>
                                <h3 className="text-lg font-medium mb-2">Links</h3>
                                <div className="overflow-x-auto">
                                    <table className="w-full border-collapse">
                                        <thead>
                                            <tr className="bg-gray-200">
                                                <th className="border p-2">Link Text</th>
                                                <th className="border p-2">URL</th>
                                                <th className="border p-2">Status</th>
                                                <th className="border p-2">Product Table Detection</th>
                                                <th className="border p-2">Issues</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {results.links.map((item, index) => (
                                                <tr key={index} className={`border ${item.has_product_table ? 'bg-green-50' : ''}`}>
                                                    <td className="border p-2">{item.link_text}</td>
                                                    <td className="border p-2">
                                                        <a
                                                            href={item.url}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="text-blue-600 hover:underline"
                                                        >
                                                            {item.url.length > 50 ? item.url.substring(0, 50) + '...' : item.url}
                                                        </a>
                                                    </td>
                                                    <td
                                                        className={`border p-2 ${
                                                            item.status === "PASS"
                                                                ? "text-green-600"
                                                                : item.status === "ERROR"
                                                                ? "text-yellow-600"
                                                                : "text-red-600"
                                                        }`}
                                                    >
                                                        {item.status}
                                                    </td>
                                                    <td className="border p-2">
                                                        {item.has_product_table !== undefined ? (
                                                            <div>
                                                                <span className={`font-semibold ${item.has_product_table ? 'text-green-600' : 'text-gray-600'}`}>
                                                                    {item.has_product_table ? 'Yes' : 'No'}
                                                                </span>
                                                                {item.has_product_table && item.product_table_class && (
                                                                    <div className="text-xs text-gray-600 mt-1">
                                                                        Class: {item.product_table_class}
                                                                    </div>
                                                                )}
                                                                {item.product_table_error && (
                                                                    <div className="text-xs text-red-500 mt-1">
                                                                        Error: {item.product_table_error}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        ) : (
                                                            <span className="text-gray-500">Not checked</span>
                                                        )}
                                                    </td>
                                                    <td className="border p-2">
                                                        {item.utm_issues.length > 0
                                                            ? (
                                                                <ul className="list-disc pl-4">
                                                                    {item.utm_issues.map((issue, i) => (
                                                                        <li key={i}>{issue}</li>
                                                                    ))}
                                                                </ul>
                                                            )
                                                            : "None"}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

ReactDOM.render(<App />, document.getElementById('root'));
