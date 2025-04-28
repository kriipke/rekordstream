import { useState } from "react";

function App() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = () => {
    window.location.href = `${process.env.REACT_APP_API_URL}/app/login`;
  };

  const handleUpload = async () => {
    if (!file) return;

    setLoading(true);
    setUploadStatus(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${process.env.REACT_APP_API_URL}/app/upload`, {
        method: "POST",
        body: formData,
        credentials: "include", // very important
      });

      if (res.ok) {
        setUploadStatus("success");
      } else {
        setUploadStatus("error");
      }
    } catch (err) {
      console.error(err);
      setUploadStatus("error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>Rekordbox to Spotify Sync</h1>
      <button onClick={handleLogin}>Login to Spotify</button>

      <div style={{ marginTop: "20px" }}>
        <input
          type="file"
          accept=".xml"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <button onClick={handleUpload} disabled={!file || loading} style={{ marginLeft: "10px" }}>
          Upload Rekordbox XML
        </button>
      </div>

      {loading && <div style={{ marginTop: "10px" }}>Uploading...</div>}

      {uploadStatus === "success" && (
        <div style={{ color: "green", marginTop: "10px" }}>✅ Upload successful!</div>
      )}

      {uploadStatus === "error" && (
        <div style={{ color: "red", marginTop: "10px" }}>❌ Upload failed. Try again.</div>
      )}
    </div>
  );
}

export default App;

