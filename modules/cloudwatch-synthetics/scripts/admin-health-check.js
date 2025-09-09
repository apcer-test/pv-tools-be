const synthetics = require("Synthetics");
const configuration = synthetics.getConfiguration();

const pageLoadBlueprint = async function () {
  const url = "https://example.com";

  const page = await synthetics.getPage();
  const response = await page.goto(url, {
    waitUntil: "networkidle0",
    timeout: 30000,
  });

  if (response.status() !== 200) {
    throw "Failed to load page";
  }

  await synthetics.addExecutionError("Custom error", "Custom error message");
};

exports.handler = async () => {
  return await pageLoadBlueprint();
};
