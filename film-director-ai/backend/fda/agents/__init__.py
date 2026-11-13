"""Agent registry: workflow task agent name → handler(ctx)."""


def _h():
    from . import audio, director, editor, quality, research, scriptwriter, storyboard, visual, voiceover
    return {"analyze": director.analyze_run, "research": research.run, "script": scriptwriter.run, "voiceover": voiceover.run, "storyboard": storyboard.run,
            "visual": visual.run, "audio": audio.run, "editor": editor.run, "render": quality.render_run, "qc": quality.qc_run, "finalize": director.finalize_run,
            "apply_edit": director.apply_edit_run}


class _Lazy(dict):
    def __missing__(self, k):
        self.update(_h())
        if k not in self:
            raise KeyError(k)
        return self[k]

    def get(self, k, d=None):
        try:
            return self[k]
        except KeyError:
            return d


HANDLERS = _Lazy()
