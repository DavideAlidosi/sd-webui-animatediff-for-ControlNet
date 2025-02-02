import os

import gradio as gr

from scripts.animatediff_mm import mm_animatediff as motion_module


class ToolButton(gr.Button, gr.components.FormComponent):
    """Small button with single emoji as text, fits inside gradio forms"""

    def __init__(self, **kwargs):
        super().__init__(variant="tool", **kwargs)

    def get_block_name(self):
        return "button"


class AnimateDiffProcess:
    def __init__(
        self,
        enable=False,
        loop_number=0,
        video_length=16,
        fps=8,
        model="mm_sd_v15_v2.ckpt",
        format=["GIF", "PNG"],
        reverse=[],
        latent_power=1,
        latent_scale=32,
        last_frame=None,
        latent_power_last=1,
        latent_scale_last=32,
    ):
        self.enable = enable
        self.loop_number = loop_number
        self.video_length = video_length
        self.fps = fps
        self.model = model
        self.format = format
        self.reverse = reverse
        self.latent_power = latent_power
        self.latent_scale = latent_scale
        self.last_frame = last_frame
        self.latent_power_last = latent_power_last
        self.latent_scale_last = latent_scale_last

    def get_list(self, is_img2img: bool):
        list_var = list(vars(self).values())
        if not is_img2img:
            list_var = list_var[:-5]
        return list_var

    def _check(self):
        assert (
            self.video_length > 0 and self.fps > 0
        ), "Video length and FPS should be positive."
        assert not set(["GIF", "MP4", "PNG"]).isdisjoint(
            self.format
        ), "At least one saving format should be selected."

    def set_p(self, p):
        self._check()
        p.batch_size = self.video_length
        if "PNG" not in self.format:
            p.do_not_save_samples = True


class AnimateDiffUiGroup:
    txt2img_submit_button = None
    img2img_submit_button = None

    def __init__(self):
        self.params = AnimateDiffProcess()

    def render(self, is_img2img: bool, model_dir: str):
        if not os.path.isdir(model_dir):
            os.mkdir(model_dir)
        model_list = [f for f in os.listdir(model_dir) if f != ".gitkeep"]
        with gr.Accordion("AnimateDiff v1.6.0 for ControlNet", open=False):
            with gr.Row():

                def refresh_models(*inputs):
                    new_model_list = [
                        f for f in os.listdir(model_dir) if f != ".gitkeep"
                    ]
                    dd = inputs[0]
                    if dd in new_model_list:
                        selected = dd
                    elif len(new_model_list) > 0:
                        selected = new_model_list[0]
                    else:
                        selected = None
                    return gr.Dropdown.update(choices=new_model_list, value=selected)

                self.params.model = gr.Dropdown(
                    choices=model_list,
                    value=(self.params.model if self.params.model in model_list else None),
                    label="Motion module",
                    type="value",
                )
                refresh_model = ToolButton(value="\U0001f504")
                refresh_model.click(
                    refresh_models, self.params.model, self.params.model
                )
            with gr.Row():
                self.params.enable = gr.Checkbox(
                    value=self.params.enable, label="Enable AnimateDiff"
                )
                self.params.video_length = gr.Slider(
                    minimum=1,
                    maximum=32,
                    value=self.params.video_length,
                    step=1,
                    label="Number of frames",
                    precision=0,
                )
                self.params.fps = gr.Number(
                    value=self.params.fps, label="Frames per second (FPS)", precision=0
                )
                self.params.loop_number = gr.Number(
                    minimum=0,
                    value=self.params.loop_number,
                    label="Display loop number (0 = infinite loop)",
                    precision=0,
                )
            with gr.Row():
                self.params.format = gr.CheckboxGroup(
                    choices=["GIF", "MP4", "PNG", "TXT"],
                    label="Save",
                    type="value",
                    value=self.params.format,
                )
                self.params.reverse = gr.CheckboxGroup(
                    choices=["Add Reverse Frame", "Remove head", "Remove tail"],
                    label="Reverse",
                    type="index",
                    value=self.params.reverse
                )
            if is_img2img:
                with gr.Row():
                    self.params.latent_power = gr.Slider(
                        minimum=0.1,
                        maximum=10,
                        value=self.params.latent_power,
                        step=0.1,
                        label="Latent power",
                    )
                    self.params.latent_scale = gr.Slider(
                        minimum=1,
                        maximum=128,
                        value=self.params.latent_scale,
                        label="Latent scale",
                    )
                    self.params.latent_power_last = gr.Slider(
                        minimum=0.1,
                        maximum=10,
                        value=self.params.latent_power_last,
                        step=0.1,
                        label="Optional latent power for last frame",
                    )
                    self.params.latent_scale_last = gr.Slider(
                        minimum=1,
                        maximum=128,
                        value=self.params.latent_scale_last,
                        label="Optional latent scale for last frame",
                    )
                self.params.last_frame = gr.Image(
                    label="[Experiment] Optional last frame. Leave it blank if you do not need one.",
                    type="pil",
                )
            with gr.Row():
                unload = gr.Button(
                    value="Move motion module to CPU (default if lowvram)"
                )
                remove = gr.Button(value="Remove motion module from any memory")
                unload.click(fn=motion_module.unload)
                remove.click(fn=motion_module.remove)
        return self.register_unit(is_img2img)

    def register_unit(self, is_img2img: bool):
        unit = gr.State()
        (
            AnimateDiffUiGroup.img2img_submit_button
            if is_img2img
            else AnimateDiffUiGroup.txt2img_submit_button
        ).click(
            fn=AnimateDiffProcess,
            inputs=self.params.get_list(is_img2img),
            outputs=unit,
            queue=False,
        )
        return unit

    @staticmethod
    def on_after_component(component, **_kwargs):
        elem_id = getattr(component, "elem_id", None)

        if elem_id == "txt2img_generate":
            AnimateDiffUiGroup.txt2img_submit_button = component
            return

        if elem_id == "img2img_generate":
            AnimateDiffUiGroup.img2img_submit_button = component
            return
