export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { id } = req.query;

    const response = await fetch(`https://api.assemblyai.com/v2/transcript/${id}`, {
      headers: {
        'Authorization': process.env.ASSEMBLYAI_API_KEY
      }
    });

    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    console.error('Error getting transcription:', error);
    res.status(500).json({ error: 'Error getting transcription' });
  }
}