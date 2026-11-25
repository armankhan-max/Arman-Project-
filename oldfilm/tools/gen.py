import torch, json, sys, os, time
from diffusers import AutoPipelineForText2Image
torch.set_num_threads(4)
pipe = AutoPipelineForText2Image.from_pretrained("stabilityai/sdxl-turbo", torch_dtype=torch.bfloat16, variant="fp16")
pipe.set_progress_bar_config(disable=True)
jobs = json.load(open(sys.argv[1])); outdir = sys.argv[2]
STYLE = ", 1950s black and white documentary photograph, monochrome, silver gelatin print, film grain, grainy, high contrast, vintage, no text"
for j in jobs:
    for v in range(j.get("n", 2)):
        p = os.path.join(outdir, f"{j['id']}_{v}.png")
        if os.path.exists(p): continue
        t = time.time()
        g = torch.Generator().manual_seed(1000 + v * 77 + hash(j['id']) % 1000)
        im = pipe(prompt=j["p"] + STYLE, num_inference_steps=4, guidance_scale=0.0, width=768, height=512, generator=g).images[0]
        im.save(p); print(p, round(time.time() - t, 1), flush=True)
