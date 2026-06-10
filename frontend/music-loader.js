// Wait until the webpage completely loads before running our data script
document.addEventListener("DOMContentLoaded", () => {
    
    // 1. Tell the browser to look for our local JSON data file
    fetch("music-data.json")
        .then(response => response.json()) // Convert the raw file data into a readable JavaScript array
        .then(musicList => {
            
            // 2. Grab a reference to our empty HTML table body
            const tableBody = document.getElementById("table-body");
            
            // 3. Clear out any old content just in case
            tableBody.innerHTML = "";
            
            // 4. Loop through each music object in our array (equivalent to a Python 'for item in musicList:')
            musicList.forEach(item => {
                
                // Create a brand new table row HTML element <tr>
                const row = document.createElement("tr");
                
                // Construct the inner cells <td> using template literals (equivalent to Python f-strings)
                row.innerHTML = `
                    <td>${item.genre}</td>
                    <td>${item.period}</td>
                    <td>${item.type}</td>
                    <td>${item.subtype}</td>
                    <td><strong>${item.piece}</strong></td>
                    <td>${item.composer}</td>
                    <td>${item.performer}</td>
                    <td><a href="${item.spotify}" target="_blank" class="spotify-link">Listen 🎧</a></td>
                `;
                
                // 5. Append this brand new row right into our actual webpage table body
                tableBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error("Error reading the music data vault:", error);
        });
});