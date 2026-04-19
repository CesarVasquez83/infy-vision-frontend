import { useState } from "react";

function App() {
  const [prompt, setPrompt] = useState("");
  const [chatRespuesta, setChatRespuesta] = useState("");
  const [imagen, setImagen] = useState(null);
  const [visionResultado, setVisionResultado] = useState("");

  // ---------------------
  // Enviar prompt a /chat
  // ---------------------
  const enviarPrompt = async () => {
    const formData = new FormData();
    formData.append("prompt", prompt);

    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    setChatRespuesta(data.respuesta);
  };

  // ---------------------
  // Enviar imagen a /vision
  // ---------------------
  const enviarImagen = async () => {
    if (!imagen) return;
    const formData = new FormData();
    formData.append("file", imagen);

    const res = await fetch("http://localhost:8000/vision", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    setVisionResultado(data.result);
  };

  return (
    <div style={{ padding: "20px", fontFamily: "sans-serif" }}>
      <h2>Chat Azure OpenAI</h2>
      <input
        type="text"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Escribe tu prompt"
        style={{ width: "300px" }}
      />
      <button onClick={enviarPrompt}>Enviar</button>
      <p><strong>Respuesta:</strong> {chatRespuesta}</p>

      <hr />

      <h2>Vision Computer</h2>
      <input
        type="file"
        accept="image/*"
        onChange={(e) => setImagen(e.target.files[0])}
      />
      <button onClick={enviarImagen}>Analizar Imagen</button>
      <p><strong>Resultado:</strong> {visionResultado}</p>
    </div>
  );
}

export default App;