const fs = require('fs');

// 1. Define your input and output file paths
const inputFile = 'r18_links.json';
const keyitem = ' III Year I Semester';
const outputFile = `${keyitem}_links.json`;

// 2. Read the original JSON file
fs.readFile(inputFile, 'utf8', (err, data) => {
    if (err) {
        console.error(`Error reading the file ${inputFile}:`, err);
        return;
    }

    try {
        // 3. Parse the raw text data into a JavaScript array
        const allLinks = JSON.parse(data);

        // 4. Filter for objects where the 'text' property includes "R18"
        const r18Links = allLinks.filter(item => item.text && item.text.includes(keyitem));


        const examCodes = r18Links.map(item => {
            try {
                // Prepend a dummy domain so the URL constructor can parse the relative path
                const url = new URL(item.href, 'https://example.com');
                return url.searchParams.get('examCode');
            } catch (e) {
                return null;
            }
        }).filter(code => code !== null); // Filter out any failed parses

        // Format the output exactly as "1962","1974"
        const uniqueReversedCodes = Array.from(new Set(examCodes));
        const formattedCodesList = uniqueReversedCodes
        
        .map(code => `"${code}"`).join(',');
        console.log('\n--- Extracted Exam Codes ---');
        console.log(formattedCodesList);
        console.log('-----------------------------\n');
        // 5. Convert the filtered array back into a readable JSON string
        // The 'null, 2' arguments format the JSON beautifully with indentation
        const jsonOutput = JSON.stringify(r18Links, null, 2);


        // 6. Write the filtered data into the new file
        fs.writeFile(outputFile, jsonOutput, 'utf8', (err) => {
            if (err) {
                console.error(`Error writing to ${outputFile}:`, err);
                return;
            }
            console.log(`Success! Filtered ${r18Links.length} items. Saved to ${outputFile}`);
        });

    } catch (parseError) {
        console.error("Error parsing JSON data. Ensure your input file is valid JSON.", parseError);
    }
});