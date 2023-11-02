document.getElementById("submit-btn").addEventListener("click", function () {
    let videoUrl = document.getElementById("videoUrl").value;

    fetch('https://j3x8u9dq2m.execute-api.us-east-1.amazonaws.com/dev', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ videoLink: videoUrl })
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById("summary").textContent = data.body;
        })
        .catch(error => {
            console.error("Error:", error);
        });
});
