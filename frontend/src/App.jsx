import { useState } from "react";
import "./App.css";

function App() {
    const [query, setQuery] = useState("");
    const [resultsData, setResultsData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // State for the Modal
    const [selectedDoc, setSelectedDoc] = useState(null);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setError(null);
        setResultsData(null);

        try {
            const response = await fetch(
                `http://127.0.0.1:5000/search?q=${encodeURIComponent(query)}`
            );

            if (!response.ok) {
                throw new Error("Failed to fetch results");
            }

            const data = await response.json();
            setResultsData(data);
        } catch (err) {
            console.error(err);
            setError("Error connecting to the search server.");
        } finally {
            setLoading(false);
        }
    };

    const openModal = (doc, e) => {
        e.preventDefault(); 
        setSelectedDoc(doc);
    };

    const closeModal = () => {
        setSelectedDoc(null);
    };

    const getFlag = (lang) => {
        switch (lang) {
            case "en":
                return "🇺🇸";
            case "es":
                return "🇪🇸";
            case "hi":
                return "🇮🇳";
            default:
                return "🌐";
        }
    };

    const getLangName = (lang) => {
        switch (lang) {
            case "en":
                return "English";
            case "es":
                return "Spanish";
            case "hi":
                return "Hindi";
            default:
                return lang.toUpperCase();
        }
    };

    return (
        <div className="app-container">
            <header>
                <h1>🧠 NeuralHybrid Search</h1>
                <p className="subtitle">
                    Advanced Information Retrieval System
                </p>
            </header>

            <div className="search-box">
                <form onSubmit={handleSearch}>
                    <div className="input-row">
                        <input
                            type="text"
                            placeholder="Search concepts (e.g., 'Economy', 'Deportes', 'अंतरिक्ष')..."
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />
                        <button type="submit" disabled={loading}>
                            {loading ? "Analyzing..." : "Search"}
                        </button>
                    </div>
                </form>
            </div>

            {error && <div className="error-msg">{error}</div>}

            {resultsData && (
                <div className="meta-info">
                    <span className="badge lang-detect">
                        Query Detected:{" "}
                        {getFlag(resultsData.query_detected_lang)}{" "}
                        {getLangName(resultsData.query_detected_lang)}
                    </span>
                    <span className="result-count">
                        Showing top {resultsData.results.length} results
                    </span>
                </div>
            )}

            <div className="results-container">
                {resultsData && resultsData.results.length > 0 ? (
                    <div className="results-list">
                        {resultsData.results.map((doc, idx) => (
                            <div key={idx} className="result-card">
                                <div className="card-header">
                                    <div className="title-group">
                                        <span
                                            className="doc-flag"
                                            title={`Result in ${getLangName(
                                                doc.lang
                                            )}`}
                                        >
                                            {getFlag(doc.lang)}
                                        </span>
                                        {/* onClick opens Modal instead of href */}
                                        <a
                                            href={doc.url}
                                            onClick={(e) => openModal(doc, e)}
                                            className="doc-title"
                                        >
                                            {doc.title}
                                        </a>
                                    </div>
                                    <span className="score-badge main">
                                        {(doc.score * 100).toFixed(0)}% Match
                                    </span>
                                </div>

                                <p className="snippet">
                                    
                                    <span
                                        onClick={(e) => openModal(doc, e)}
                                        style={{ cursor: "pointer" }}
                                    >
                                        {(() => {
                                            // 1. Get the content safely (fallback to empty string if missing)
                                            const content =
                                                doc.summary || doc.text || "";

                                            // 2. Truncate if longer than 100 characters
                                            return content.length > 100
                                                ? content.substring(0, 100) +
                                                      "..."
                                                : content;
                                        })()}
                                    </span>
                                </p>

                                <div className="score-breakdown">
                                    <div className="score-item">
                                        <span className="label">
                                            Semantic (AI):
                                        </span>
                                        <div className="bar-container">
                                            <div
                                                className="bar semantic"
                                                style={{
                                                    width: `${
                                                        doc.semantic_score * 100
                                                    }%`,
                                                }}
                                            ></div>
                                        </div>
                                        <span className="score-val">
                                            {(doc.semantic_score * 100).toFixed(
                                                0
                                            )}
                                            %
                                        </span>
                                    </div>
                                    <div className="score-item">
                                        <span className="label">
                                            Keyword (BM25):
                                        </span>
                                        <div className="bar-container">
                                            <div
                                                className="bar bm25"
                                                style={{
                                                    width: `${
                                                        doc.bm25_score * 100
                                                    }%`,
                                                }}
                                            ></div>
                                        </div>
                                        <span className="score-val">
                                            {(doc.bm25_score * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                </div>

                                {/* Footer link trigger modal */}
                                <a
                                    href={doc.url}
                                    onClick={(e) => openModal(doc, e)}
                                    className="url-text"
                                >
                                    Read Summary & Visit &rarr;
                                </a>
                            </div>
                        ))}
                    </div>
                ) : (
                    !loading &&
                    resultsData && (
                        <div className="no-results">
                            No documents found matching your query.
                        </div>
                    )
                )}
            </div>

            {/* --- MODAL POPUP --- */}
            {selectedDoc && (
                <div className="modal-overlay" onClick={closeModal}>
                    <div
                        className="modal-content"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <button className="close-btn" onClick={closeModal}>
                            &times;
                        </button>

                        <div className="modal-header">
                            <h2>
                                {getFlag(selectedDoc.lang)} {selectedDoc.title}
                            </h2>
                        </div>

                        <div className="modal-body">
                            <p className="modal-text">
                                <strong>Summary/Excerpt:</strong>
                                <br />
                                {selectedDoc.summary || selectedDoc.text}
                            </p>

                            <div className="modal-stats">
                                <div className="stat">
                                    AI Confidence:{" "}
                                    <strong>
                                        {(
                                            selectedDoc.semantic_score * 100
                                        ).toFixed(1)}
                                        %
                                    </strong>
                                </div>
                                <div className="stat">
                                    Keyword Match:{" "}
                                    <strong>
                                        {(selectedDoc.bm25_score * 100).toFixed(
                                            1
                                        )}
                                        %
                                    </strong>
                                </div>
                            </div>
                        </div>

                        <div className="modal-footer">
                            <a
                                href={selectedDoc.url}
                                target="_blank"
                                rel="noreferrer"
                                className="visit-btn"
                            >
                                Visit Original Article ↗
                            </a>
                            <button className="cancel-btn" onClick={closeModal}>
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default App;
