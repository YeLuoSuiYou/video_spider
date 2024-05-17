import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor

import torch
from PIL import Image
from torchvision import transforms
from tqdm import tqdm

save_path = "/qiguojun/story/howto"
output_path = "/qiguojun/story/howto_dedup"
os.makedirs(output_path, exist_ok=True)


transform = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
    ]
)

device = "cuda" if torch.cuda.is_available() else "cpu"

# model = torch.hub.load("facebookresearch/dino:main", "dino_vitb8")
# torch.hub.set_dir("/liujinxiu/ye/models/torch_hub")
model = torch.hub.load("facebookresearch/dinov2", "dinov2_vitb14")
model.eval().cuda()


@torch.inference_mode()
def image_dedup_reg(image_path, out_path):
    pre_feature = torch.zeros(1, 768).to(device)
    pre_i_path = ""

    # sort according to the numerical order instead of alphabetic order
    def fns(s):
        return sum(((s, int(n)) for s, n in re.findall("(\\D+)(\\d+)", "a%s0" % s)), ())

    l = len(sorted(os.listdir(image_path), key=fns))
    i = 0

    for image_name in sorted(os.listdir(image_path), key=fns):
        i_path = image_path + "/" + image_name
        o_path = out_path + "/" + image_name

        if os.path.splitext(os.path.basename(i_path))[1] == ".jpg":
            image = transform(Image.open(i_path)).unsqueeze(0).to(device)  # type: ignore

            image_feature = model(image)
            similarity = torch.cosine_similarity(image_feature, pre_feature, dim=1)

            # if similarity.item() >= 0.75:
            #     # print(i_path + ":  " + str(similarity.item()))
            #     if os.path.isfile(pre_i_path):
            #         os.remove(pre_i_path)
            # else:
            #     pre_feature = image_feature
            if similarity.item() < 0.75:
                shutil.copy2(i_path, o_path)

            pre_i_path = i_path

            i += 1

    torch.cuda.empty_cache()


def process_folder(video_no):
    image_path = save_path + "/" + video_no
    out_path = output_path + "/" + video_no
    if os.path.exists(out_path):
        return
    os.makedirs(out_path)
    try:
        image_dedup_reg(image_path, out_path)
        # print("Finished Video: " + video_no)
    except Exception:
        print("Failed Video: " + video_no)


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=8) as executor:
        folders = sorted(os.listdir(save_path))
        list(tqdm(executor.map(process_folder, folders), total=len(folders)))
