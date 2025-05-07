// Test case 1: metadata as object
const dataWithObjectMetadata = {
    metadata: {
        sender: "test@example.com",
        sender_name: "Test Sender",
        reply_to: "reply@example.com",
        subject: "Test Subject",
        preheader: "Test Preheader"
    },
    links: []
};

// Test case 2: metadata as array
const dataWithArrayMetadata = {
    metadata: [
        {
            field: "sender",
            expected: "test@example.com",
            actual: "test@example.com",
            status: "PASS"
        },
        {
            field: "sender_name",
            expected: "Test Sender",
            actual: "Test Sender",
            status: "PASS"
        }
    ],
    links: []
};

// Simulate frontend processing
function processMetadata(data) {
    console.log("Processing metadata...");
    
    let allMetadata = [];
    
    if (data.metadata) {
        // Check if metadata is already in array format
        if (Array.isArray(data.metadata)) {
            console.log("Metadata is an array, using directly");
            allMetadata = [...data.metadata];
        } else {
            console.log("Metadata is an object, converting to array");
            // Convert object format to array format
            for (const [key, value] of Object.entries(data.metadata)) {
                allMetadata.push({
                    field: key,
                    actual: value || 'Not found',
                    expected: key === 'sender' ? 'test@example.com' : '',
                    status: key === 'sender' ? 'PASS' : 'INFO'
                });
            }
        }
    }
    
    return allMetadata;
}

// Process both test cases
console.log("Result with object metadata:", processMetadata(dataWithObjectMetadata));
console.log("Result with array metadata:", processMetadata(dataWithArrayMetadata));