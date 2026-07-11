import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  try {
    // 1. Supabase 대시보드에 저장할 환경변수 읽어오기
    const TOKEN = Deno.env.get("TELEGRAM_BOT_TOKEN");
    const CHAT_ID = Deno.env.get("TELEGRAM_CHAT_ID");

    if (!TOKEN || !CHAT_ID) {
      return new Response("환경변수(Secrets) 설정이 누락되었습니다.", { status: 500 });
    }

    // 2. 한국 시간 계산 (UTC + 9시간)
    const now = new Date();
    const kstOffset = 9 * 60 * 60 * 1000;
    const kstDate = new Date(now.getTime() + kstOffset);
    const timeString = kstDate.toISOString().replace('T', ' ').substring(0, 19);

    // 3. 텔레그램 발송 메시지 구성
    const message = `🔔 [Supabase 정시 테스트] 현재 한국 시간은 ${timeString} 입니다.`;

    // 4. 텔레그램 API 호출
    const telegramUrl = `https://api.telegram.org/bot${TOKEN}/sendMessage`;
    const response = await fetch(telegramUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: CHAT_ID,
        text: message,
      }),
    });

    const result = await response.json();

    return new Response(JSON.stringify({ success: true, result }), {
      headers: { "Content-Type": "application/json" },
    });

  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
})