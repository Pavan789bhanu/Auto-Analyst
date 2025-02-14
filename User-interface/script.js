const backendUrl = "http://52.62.18.64:5000"; // Replace with your backend URL
let accessToken = null;

async function login() {
  const username = document.getElementById("username").value;
  const password = document.getElementById("password").value;

  try {
    const response = await fetch(`${backendUrl}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json();

    if (response.ok) {
      accessToken = data.access_token;
      document.getElementById("loginMessage").innerText = "Login successful!";
      document.getElementById("login").style.display = "none";
      document.getElementById("upload").style.display = "block";
      document.getElementById("query").style.display = "block";
      document.getElementById("results").style.display = "block";
    } else {
      document.getElementById("loginMessage").innerText = data.message || "Login failed.";
    }
  } catch (error) {
    console.error("Error:", error);
  }
}

async function uploadFile() {
  const fileInput = document.getElementById("fileInput").files[0];
  const formData = new FormData();
  formData.append("file", fileInput);

  try {
    const response = await fetch(`${backendUrl}/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
      body: formData,
    });

    const data = await response.json();
    document.getElementById("uploadMessage").innerText = data.message || "Upload failed.";
  } catch (error) {
    console.error("Error:", error);
  }
}

async function submitQuery() {
  const query = document.getElementById("queryInput").value;

  try {
    const response = await fetch(`${backendUrl}/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ query }),
    });

    const data = await response.json();
    document.getElementById("queryMessage").innerText = data.message || "Query submission failed.";
  } catch (error) {
    console.error("Error:", error);
  }
}

async function fetchResults() {
  try {
    const response = await fetch(`${backendUrl}/results`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    const results = await response.json();
    const resultsList = document.getElementById("resultsList");
    resultsList.innerHTML = results.map((result) => `<li>${JSON.stringify(result)}</li>`).join("");
  } catch (error) {
    console.error("Error:", error);
  }
}
