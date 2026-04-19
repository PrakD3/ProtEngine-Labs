import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const { messages, system } = await req.json();

    const apiKey = process.env.GROQ_API_KEY;
    if (!apiKey) {
      return NextResponse.json({ error: "No GROQ_API_KEY set" }, { status: 500 });
    }

    // Convert Anthropic style separate system message into OpenAI style array
    const formattedMessages = [
      { role: "system", content: system },
      ...messages
    ];

    const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "llama-3.3-70b-versatile",
        messages: formattedMessages,
        max_tokens: 1500,
        temperature: 0.7,
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      return NextResponse.json({ error: err }, { status: response.status });
    }

    const data = await response.json();
    
    // Remap the OpenAI style response back to the format the frontend currently expects 
    // (Our frontend expects the Anthropic format data.content[0].text)
    return NextResponse.json({
      content: [
        { text: data.choices?.[0]?.message?.content || "No response generated." }
      ]
    });
  } catch (err: any) {
    return NextResponse.json({ error: err.message }, { status: 500 });
  }
}
