# Providers

Configure in **Settings → Providers** (stored encrypted) or with the environment variable shown. “Verified” means the
adapter has been exercised against the real service in development; “awaiting credentials” means it follows the
vendor's public documentation but has not been run with a real key yet.

| Provider | Capability | Cost | Needs | State |
| --- | --- | --- | --- | --- |
| Anthropic Claude | reasoning (Director, writer, storyboard, QC) | paid | `ANTHROPIC_API_KEY` | awaiting credentials |
| OpenAI | reasoning, images, transcription, embeddings | paid | `OPENAI_API_KEY` | awaiting credentials |
| Groq | reasoning | paid/free tier | `GROQ_API_KEY` | awaiting credentials |
| Pollinations text | reasoning fallback | free | – | verified |
| Pollinations images (FLUX) | AI stills | free | – | verified |
| Runway | image→video | paid | `RUNWAYML_API_SECRET` | awaiting credentials |
| Luma Dream Machine | text/image→video | paid | `LUMAAI_API_KEY` | awaiting credentials |
| Pexels | stock video & photos | free | `PEXELS_API_KEY` | awaiting credentials |
| Pixabay | stock video & photos | free | `PIXABAY_API_KEY` | awaiting credentials |
| Wikimedia Commons | archive photos/video, PD/CC only | free | – | verified |
| NASA Image Library | space archive | free | – | built (host blocked in the dev sandbox) |
| Wikipedia | research sources | free | – | built (host blocked in the dev sandbox) |
| Tavily | web search for research | paid | `TAVILY_API_KEY` | awaiting credentials |
| Edge neural voices | TTS with word timings | free | – | verified |
| ElevenLabs | TTS with alignment | paid | `ELEVENLABS_API_KEY` | awaiting credentials |
| faster-whisper (local) | transcription, word timestamps | free | model download on first use | built (model host blocked in the dev sandbox) |
| D-ID | talking avatars | paid | `DID_API_KEY` | awaiting credentials |
| Talking photo (built in) | approximate avatar animation | free | – | verified |
| Blender | 3D scenes | free | `blender` on PATH | verified |
| Procedural audio | original music & SFX | free | – | verified |
| YouTube Data API | public research | free quota | `YOUTUBE_API_KEY` | awaiting credentials |
| Google OAuth + YouTube Analytics | your channel analytics (read-only) | free | OAuth client ID/secret | awaiting credentials |

## Paid providers and budgets

A paid call is reserved before it runs: the registry multiplies your **USD per unit** estimate (entered per provider)
by the planned units and checks daily, monthly, project and provider limits. Nothing paid runs when no daily or
monthly limit exists or when the estimate is missing. Prices are never invented; actual usage (tokens, characters,
seconds) is recorded after each call.

## Google OAuth setup

1. Google Cloud Console → create a project → enable *YouTube Data API v3* and *YouTube Analytics API*.
2. OAuth consent screen (External, add yourself as a test user). Scopes: `youtube.readonly`, `yt-analytics.readonly`.
3. Credentials → OAuth client ID → Web application → Authorised redirect URI:
   `FDA_PUBLIC_BASE_URL/api/v1/youtube/oauth/callback` (default `http://localhost:8000/api/v1/youtube/oauth/callback`).
4. Paste client ID and secret into Settings → Providers → Google OAuth, then YouTube Intelligence → Connect.

Impressions and click-through rate are not exposed by the YouTube Analytics API v2; the dashboard says so instead of
showing a number.

## Adding a provider

Subclass the capability base (`LLMProvider`, `ImageProvider`, `VideoProvider`, `TTSProvider`, `STTProvider`,
`AvatarProvider`, or `Provider` with a `search()` for stock/archive), declare `caps`, `paid`, `fields`, `unit`,
implement the call and `validate()`, add the class to `FACTORIES` and, if it should be preferred, to `PREFERENCE`
in `fda/providers/registry.py`. Agents pick it up by capability; no other file names vendors.
