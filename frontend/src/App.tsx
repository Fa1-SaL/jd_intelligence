import { useState, useRef } from 'react';

export default function App() {
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [jobUrl, setJobUrl] = useState('');
  const [rawJd, setRawJd] = useState('');
  const [structuredJd, setStructuredJd] = useState('');
  const [emailTemplate, setEmailTemplate] = useState('');
  const [suggestedTitles, setSuggestedTitles] = useState('');
  const [error, setError] = useState<string | null>(null);

  const jdRef = useRef<HTMLDivElement>(null);
  const emailRef = useRef<HTMLDivElement>(null);

  const handleGenerate = async () => {
    if (!rawJd.trim() && !jobUrl.trim()) {
      setError('Please provide a job link or paste the job description.');
      return;
    }

    setStep(2);
    setError(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/parse-jd", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ raw_jd: rawJd, url: jobUrl })
      });

      const data = await res.json();

      setStructuredJd(data.jd || "");
      setEmailTemplate(data.email || "");
      setSuggestedTitles((data.titles || []).join("\n"));

      setStep(3);
    } catch (err: any) {
      setError(err.message || "Error processing your request.");
      setStep(1);
    }
  };

  const copyHtml = async (html: string) => {
    const blob = new Blob([html], { type: "text/html" });
    const data = [new ClipboardItem({ "text/html": blob })];
    await navigator.clipboard.write(data);
  };
  //Name suggested by Samarth
  return (
    <div className="layout-root">

      {step !== 2 && (
        <nav className="nav-top">
          <div className="nav-left">
            <span className="logo">Job Weaver</span>
            {step === 1 && <span className="logo-sub">CROSSING HURDLES</span>}
          </div>

          <div className="nav-right">
            {step === 1 && (
              <div className="step-indicator">
                STEP 1 OF 2
                <div className="progress-bars">
                  <div className="bar active"></div>
                  <div className="bar"></div>
                </div>
              </div>
            )}
            {step === 3 && (
              <>
                <div className="step-indicator">
                  STEP 2 OF 2
                  <div className="progress-bars">
                    <div className="bar active"></div>
                    <div className="bar active"></div>
                  </div>
                </div>
                <button className="btn-back" onClick={() => setStep(1)}>
                  <ArrowLeftIcon /> Back to Input
                </button>
              </>
            )}
          </div>
        </nav>
      )}

      <main className="main-content">

        {step === 1 && (
          <div className="wizard-input-view">
            <div className="hero">
              <h1>Define Your Search</h1>
              <p>Paste the job description below to begin the structural analysis<br />of role requirements and latent expectations.</p>
            </div>

            <div className="card form-card">
              <label className="input-label">JOB LINK (REFERRAL)</label>
              <div className="input-with-icon" style={{ marginBottom: "24px" }}>
                <LinkIcon />
                <input
                  type="text"
                  className="input-field-clean"
                  placeholder="https://linkedin.com/jobs/view/..."
                  value={jobUrl}
                  onChange={(e) => setJobUrl(e.target.value)}
                />
              </div>

              <label className="input-label">PASTE RAW JOB DESCRIPTION</label>
              <textarea
                className="input-field-clean textarea-large"
                placeholder="Copy and paste the full description here..."
                value={rawJd}
                onChange={(e) => setRawJd(e.target.value)}
              />

              {error && <p className="error-text">{error}</p>}

              <div className="form-actions">
                <button
                  className="btn-ghost"
                  onClick={() => { setRawJd(''); setJobUrl(''); }}
                >
                  Clear
                </button>
                <button className="btn-primary" onClick={handleGenerate}>
                  Generate Analysis <ArrowRightIcon />
                </button>
              </div>
            </div>

            <div className="version-label">V1.5 (PROTOTYPE)</div>
          </div>
        )}

        {step === 2 && (
          <div className="wizard-processing-view">
            <h2>Processing...</h2>
            <p>Architectural analysis in progress</p>
          </div>
        )}

        {step === 3 && (
          <div className="wizard-output-view">

            <div className="output-col-left">
              <div className="output-section">
                <div className="section-header">
                  <div>
                    <h3>Outreach Email</h3>

                  </div>
                  <div className="header-actions">
                    <button className="btn-ghost-box"><EditIcon /> Edit</button>
                    <button className="btn-primary-box" onClick={() => copyHtml(emailTemplate)}>
                      <CopyIcon /> Copy Template
                    </button>
                  </div>
                </div>
                <div className="card output-card">
                  <div
                    className="rich-text-content"
                    ref={emailRef}
                    contentEditable
                    dangerouslySetInnerHTML={{ __html: emailTemplate || "<p>No data</p>" }}
                  />
                </div>
              </div>

              <div className="output-section" style={{ marginTop: "48px" }}>
                <div className="section-header">
                  <div>
                    <h3>Job Description</h3>

                  </div>
                  <div className="header-actions">
                    <button className="btn-ghost-box"><EditIcon /> Edit</button>
                    <button className="btn-primary-box" onClick={() => copyHtml(structuredJd)}>
                      <CopyIcon /> Copy JD
                    </button>
                  </div>
                </div>
                <div className="card output-card">
                  <div
                    className="rich-text-content"
                    ref={jdRef}
                    contentEditable
                    dangerouslySetInnerHTML={{ __html: structuredJd || "<p>No data</p>" }}
                  />
                </div>
              </div>
            </div>

            <div className="output-col-right">
              <div className="card gray-card">
                <div className="mini-title">SUGGESTED TITLES</div>
                <ul className="bullet-list">
                  {suggestedTitles.split("\n").filter(Boolean).map((t, i) => (
                    <li key={i}>{t.replace(/^- /, '').trim()}</li>
                  ))}
                </ul>
              </div>

              <div className="card dashed-placeholder">
                <div className="placeholder-icon"><BriefcaseIcon /></div>
                <h4>SIMILAR JOBS</h4>
                <p>No matches found for the<br />current JD profile.</p>
              </div>
            </div>

          </div>
        )}
      </main>
    </div>
  );
}

// Inline SVGs tailored for the mockups
const LinkIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
  </svg>
);

const ArrowRightIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="5" y1="12" x2="19" y2="12" />
    <polyline points="12 5 19 12 12 19" />
  </svg>
);

const ArrowLeftIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="19" y1="12" x2="5" y2="12" />
    <polyline points="12 19 5 12 12 5" />
  </svg>
);

const EditIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
  </svg>
);

const CopyIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
  </svg>
);

const BriefcaseIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
  </svg>
);