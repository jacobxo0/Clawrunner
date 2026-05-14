# fal.ai — billedgenerering (Stable Diffusion, FLUX)

Generer professionelle billeder via fal.ai's API. Bruger FLUX.1 (state-of-the-art,
bedre end SD 2.0) og koster ~$0.003-0.005 per billede.

## Endpoint

```
POST https://fal.run/fal-ai/flux/schnell
Content-Type: application/json
Authorization: Key ${FAL_API_KEY}
```

## Modeller

| Model | Kvalitet | Pris | Bedst til |
|-------|----------|------|-----------|
| `fal-ai/flux/schnell` | God | ~$0.003 | Hurtige drafts, social media |
| `fal-ai/flux/dev` | Høj | ~$0.025 | Investor-materiale, præsentationer |
| `fal-ai/stable-diffusion-v3-medium` | Høj | ~$0.004 | Fotorealistisk |

## Request

```json
{
  "prompt": "professional tech startup presentation slide, clean minimal design, blue gradient, 2026 aesthetic",
  "image_size": "landscape_16_9",
  "num_inference_steps": 4,
  "num_images": 1
}
```

- `image_size`: `square_hd`, `landscape_16_9`, `portrait_4_3`
- `num_inference_steps`: 4 (schnell) eller 28 (dev) — lav for schnell

## Kald via ai-core

```json
POST ${AI_CORE_URL}/command
{
  "command": "fetch_url",
  "arguments": {
    "url": "https://fal.run/fal-ai/flux/schnell",
    "method": "POST",
    "headers": { "Authorization": "Key ${FAL_API_KEY}", "Content-Type": "application/json" },
    "body": {
      "prompt": "...",
      "image_size": "landscape_16_9",
      "num_inference_steps": 4,
      "num_images": 1
    }
  }
}
```

## Svar

```json
{
  "images": [{ "url": "https://fal.media/files/xxx.png", "width": 1920, "height": 1080 }],
  "timings": { "inference": 1.2 }
}
```

Brug `images[0].url` til at vise eller downloade billedet.

## Prompt-guide til marketing

- **Investor pitch:** `"clean minimal infographic, professional, blue/white palette, data visualization, 2026 tech startup"`
- **Social media:** `"eye-catching social post, bold typography space, gradient background, modern"`
- **Produktvisual:** `"product mockup, clean studio background, professional photography style"`

## Hvornår bruges den

- Investor pitch: slides, cover-billeder, data-visualiseringer
- Social media posts (LinkedIn, Twitter)
- Thumbnail til blogindlæg eller Notion-sider
- Brand-materiale til nye projekter
