# model template
import sys
sys.path.append('../')
from typing import List, Tuple, Any, Dict
from transformers import AutoTokenizer
from tokenizer import Tokenizer
from dataclasses import dataclass
import warnings

class Templator:
    def __init__(self, tokenizer: Tokenizer = None):
        self.tokenizer:Tokenizer = tokenizer

    def wrap(self, messages:List) -> str:
        pass
    
    @classmethod
    def generate_structured_input(
        cls, 
        messages: List[Dict],
        system_template:str,
        user_template:str,
        assistant_template:str,
        assistant_template_left:str,
        assistant_template_right:str,
        splitter:str,
        final_input:str = "",
        structured_final_input: List[str] = [""],
        # just for the inference
        add_special_token_when_last_role_is_user:bool = True,
    ) -> List[str]:
        for message in messages:
            # Our goal is to get the some part segament that can be concatenated directly and to mask some part segament
            if message['role'] == 'system':
                if system_template == None:
                    warnings.warn("The current templator is not supported the role `system`. Now we ignore the content in the system role.")
                else:
                    final_input = f"{final_input}{system_template.format(prompt=message['content'])}{splitter}"
                    structured_final_input[-1] = f"{structured_final_input[-1]}{system_template.format(prompt=message['content'])}{splitter}"
            elif message['role'] == 'user':
                final_input = f"{final_input}{user_template.format(prompt=message['content'])}{splitter}"
                structured_final_input[-1] = f"{structured_final_input[-1]}{user_template.format(prompt=message['content'])}{splitter}"
            elif message['role'] == 'assistant':
                final_input = f"{final_input}{assistant_template.format(prompt=message['content'])}{splitter}"
                structured_final_input[-1] = f"{structured_final_input[-1]}{assistant_template_left}"
                structured_final_input.append(message['content']+assistant_template_right)
                structured_final_input.append(f"{splitter}")
            else:
                raise ValueError(f"the role `{message['role']}` is not supported. Our supported role list is `[system, user, assistant]`.")
        if len(splitter) > 0:
            # remove the last splitter
            assert final_input.endswith(splitter)
            final_input = final_input[:-len(splitter)]
            assert structured_final_input[-1].endswith(splitter)
            structured_final_input[-1] = structured_final_input[-1][:-len(splitter)]
        if add_special_token_when_last_role_is_user and messages[-1]['role'] == 'user':
            structured_final_input[-1] = f"{structured_final_input[-1]}{splitter}{assistant_template_left}"
            final_input = f"{final_input}{splitter}{assistant_template_left}"
        assert final_input == "".join(structured_final_input)
        return structured_final_input

class AutoTemplator:
    def __init__(self, tokenizer: AutoTokenizer):
        self.tokenizer = tokenizer


class Qwen2Templator(Templator):
    # no explicit system prompt
    """<|im_start|>system
You are a helpful assistant<|im_end|>
<|im_start|>user
user input 1<|im_end|>
<|im_start|>assistant
model output 1<|im_end|>"""
    # explicit system prompt
    """<|im_start|>system
system prompt 1<|im_end|>
<|im_start|>user
user input 1<|im_end|>
<|im_start|>assistant
model output 1<|im_end|>"""
    @classmethod
    def wrap(cls, messages:List[Dict], add_special_token_when_last_role_is_user:bool=False, force_system_prompt:bool=False) -> List[str]:
        # no bos and no eos
        default_system_prompt = "You are a helpful assistant"
        system_template = "<|im_start|>system\n{prompt}<|im_end|>"
        user_template = "<|im_start|>user\n{prompt}<|im_end|>"
        assistant_template = "<|im_start|>assistant\n{prompt}<|im_end|>"
        assistant_template_left = "<|im_start|>assistant\n"
        assistant_template_right = "<|im_end|>"
        splitter = "\n"

        if force_system_prompt:
            is_existed = False
            for message in messages:
                if message['role'] == 'system':
                    is_existed = True
                    break
            if is_existed == False:
                messages = [{"role": "system", "content": default_system_prompt}] + messages

        return cls.generate_structured_input(
            messages=messages,
            system_template=system_template,
            user_template=user_template,
            assistant_template=assistant_template,
            assistant_template_left=assistant_template_left,
            assistant_template_right=assistant_template_right,
            splitter=splitter,
            add_special_token_when_last_role_is_user=add_special_token_when_last_role_is_user
        )
        # final_input:str = ""
        # structured_final_input: List = [""]
        # for message in messages:
        #     # Our goal is to get the some part segament that can be concatenated directly and to mask some part segament
        #     if message['role'] == 'system':
        #         final_input = f"{final_input}{system_template.format(prompt=message['content'])}{splitter}"
        #         structured_final_input[-1] = f"{structured_final_input[-1]}{system_template.format(prompt=message['content'])}{splitter}"
        #     elif message['role'] == 'user':
        #         final_input = f"{final_input}{user_template.format(prompt=message['content'])}{splitter}"
        #         structured_final_input[-1] = f"{structured_final_input[-1]}{user_template.format(prompt=message['content'])}{splitter}"
        #     elif message['role'] == 'assistant':
        #         final_input = f"{final_input}{assistant_template.format(prompt=message['content'])}{splitter}"
        #         structured_final_input[-1] = f"{structured_final_input[-1]}{assistant_template_left}"
        #         structured_final_input.append(message['content']+assistant_template_right)
        #         structured_final_input.append(f"{splitter}")
        #     else:
        #         raise ValueError(f"the role `{message['role']}` is not supported. Our supported role list is `[system, user, assistant]`.")
        # if len(splitter) > 0:
        #     # remove the last splitter
        #     assert final_input.endswith(splitter)
        #     final_input = final_input[:-len(splitter)]
        #     assert structured_final_input[-1].endswith(splitter)
        #     structured_final_input[-1] = structured_final_input[-1][:-len(splitter)]
        # assert final_input == "".join(structured_final_input)
        # return structured_final_input

class Llama2Templator(Templator):
    # no explicit system prompt
    """<s>[INST] user input 1 [/INST] model output 1 </s>"""
    # explicit system prompt
    """<s>[INST] <<SYS>>
system prompt 1
<</SYS>>

user input 1 [/INST] model output 1 </s><s>[INST] user input 2 [/INST] model output 2 </s>"""
    
    @classmethod
    def wrap(cls, messages:List, add_special_token_when_last_role_is_user:bool=False) -> List[str]:
        # multi-round is not supported by official implementation
        default_system_prompt = None
        system_template = "<<SYS>>\n{prompt}\n<</SYS>>\n\n"
        user_template = "<s>[INST] {prompt} [/INST]"
        assistant_template = " {prompt} </s>"
        assistant_template_left = " "
        assistant_template_right = " </s>"
        splitter = ""
        # if system role is shown in messages, then we first make the system_template; we finally concatenate the system_template and user_prompt to input the user_template
        final_input:str = ""
        structured_final_input: List = [""]

        # check if the system role in the messages
        if messages[0]['role'] == 'system':
            assert messages[1]['role'] == 'user'
            final_input = user_template.format(
                prompt=system_template.format(prompt=messages[0]['content']) + messages[1]['content']
            )
            structured_final_input[-1] = final_input
            messages = messages[2:]
        
        return cls.generate_structured_input(
            messages=messages,
            system_template=system_template,
            user_template=user_template,
            assistant_template=assistant_template,
            assistant_template_left=assistant_template_left,
            assistant_template_right=assistant_template_right,
            splitter=splitter,
            final_input=final_input,
            structured_final_input=structured_final_input,
            add_special_token_when_last_role_is_user=add_special_token_when_last_role_is_user
        )

        # for message in messages:
        #     # Our goal is to get the some part segament that can be concatenated directly and to mask some part segament
        #     if message['role'] == 'system':
        #         final_input = f"{final_input}{system_template.format(prompt=message['content'])}{splitter}"
        #         structured_final_input[-1] = f"{structured_final_input[-1]}{system_template.format(prompt=message['content'])}{splitter}"
        #     elif message['role'] == 'user':
        #         final_input = f"{final_input}{user_template.format(prompt=message['content'])}{splitter}"
        #         structured_final_input[-1] = f"{structured_final_input[-1]}{user_template.format(prompt=message['content'])}{splitter}"
        #     elif message['role'] == 'assistant':
        #         final_input = f"{final_input}{assistant_template.format(prompt=message['content'])}{splitter}"
        #         structured_final_input[-1] = f"{structured_final_input[-1]}{assistant_template_left}"
        #         structured_final_input.append(message['content']+assistant_template_right)
        #         structured_final_input.append(f"{splitter}")
        #     else:
        #         raise ValueError(f"the role `{message['role']}` is not supported. Our supported role list is `[system, user, assistant]`.")
        # if len(splitter) > 0:
        #     # remove the last splitter
        #     assert final_input.endswith(splitter)
        #     final_input = final_input[:-len(splitter)]
        #     assert structured_final_input[-1].endswith(splitter)
        #     structured_final_input[-1] = structured_final_input[-1][:-len(splitter)]
        # assert final_input == "".join(structured_final_input)
        # return structured_final_input

class Llama3Templator(Templator):
    # no explicit system prompt
    """<|begin_of_text|><|start_header_id|>user<|end_header_id|>

user input 1<|eot_id|><|start_header_id|>assistant<|end_header_id|>

model output 1<|eot_id|>"""
    # explicit system prompt
    """<|begin_of_text|><|start_header_id|>system<|end_header_id|>

system prompt 1<|eot_id|><|start_header_id|>user<|end_header_id|>

user input 1<|eot_id|><|start_header_id|>assistant<|end_header_id|>

model output 1<|eot_id|>"""
    @classmethod
    def wrap(cls, messages:List, add_special_token_when_last_role_is_user:bool=False) -> str:
        default_system_prompt = None
        system_template = "<|start_header_id|>system<|end_header_id|>\n\n{prompt}<|eot_id|>"
        user_template = "<|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|>"
        assistant_template = "<|start_header_id|>assistant<|end_header_id|>\n\n{prompt}<|eot_id|>"
        assistant_template_left = "<|start_header_id|>assistant<|end_header_id|>\n\n"
        assistant_template_right = "<|eot_id|>"
        splitter = ""

        return cls.generate_structured_input(
            messages=messages,
            system_template=system_template,
            user_template=user_template,
            assistant_template=assistant_template,
            assistant_template_left=assistant_template_left,
            assistant_template_right=assistant_template_right,
            splitter=splitter,
            final_input = "<|begin_of_text|>",
            structured_final_input = ["<|begin_of_text|>"],
            add_special_token_when_last_role_is_user=add_special_token_when_last_role_is_user
        )


class MistralTemplator(Templator):
    # no explicit system prompt
    """<s>[INST] user input 1[/INST] model output 1</s>"""
    # explicit system prompt
    """<s>[INST] user input 1[/INST] model output 1</s>"""
    @classmethod
    def wrap(cls, messages:List, add_special_token_when_last_role_is_user:bool=False) -> str:
        default_system_prompt = None
        system_template = None
        user_template = "[INST] {prompt}"
        assistant_template = "[/INST] {prompt}</s>"
        assistant_template_left = "[/INST] "
        assistant_template_right = "</s>"
        splitter = ""
        return cls.generate_structured_input(
            messages=messages,
            system_template=system_template,
            user_template=user_template,
            assistant_template=assistant_template,
            assistant_template_left=assistant_template_left,
            assistant_template_right=assistant_template_right,
            splitter=splitter,
            final_input = "<s>",
            structured_final_input = ["<s>"],
            add_special_token_when_last_role_is_user=add_special_token_when_last_role_is_user
        )

class GemmaTemplator(Templator):
    # no explicit system prompt
    """<bos><start_of_turn>user
user input 1<end_of_turn>
<start_of_turn>model
model output 1<end_of_turn>
<start_of_turn>user
user input 2<end_of_turn>
<start_of_turn>model
model output 2<end_of_turn>"""
    # explicit system prompt
    # system role not supported
    @classmethod
    def wrap(cls, messages:List) -> str:
        # system role is not supported by official
        default_system_prompt = None
        system_template = "<start_of_turn>system\n{prompt}<end_of_turn>"
        user_template = "<start_of_turn>user\n{prompt}<end_of_turn>"
        assistant_template = "<start_of_turn>model\n{prompt}<end_of_turn>"
        assistant_template_left = "<start_of_turn>model\n"
        assistant_template_right = "<end_of_turn>"
        splitter = "\n"
        return cls.generate_structured_input(
            messages=messages,
            system_template=system_template,
            user_template=user_template,
            assistant_template=assistant_template,
            assistant_template_left=assistant_template_left,
            assistant_template_right=assistant_template_right,
            splitter=splitter,
            final_input = "<bos>",
            structured_final_input = ["<bos>"],
        )

if __name__ == '__main__':
    # TODO: ATTENTION! Set an argument for inference. Because when inference, you need add special token to let model output.
    data = [
        {'role': 'system', 'content': 'system prompt 1'},
        {'role': 'user', 'content': 'user input 1'},
        {'role': 'assistant', 'content': 'model output 1'},
        {'role': 'user', 'content': 'user input 2'},
        {'role': 'assistant', 'content': 'model output 2'},
    ]

    tokenizer_check_list = [
        ["/disk/disk_20T/share/Llama-3-8B-Instruct", Llama3Templator, {"messages": data}],
        ["/disk/disk_20T/share/Qwen2-7B", Qwen2Templator, {"messages": data, "force_system_prompt": True}],
        ["/disk/disk_20T/qiaoshuofei/PLMs/llama-2-7b-chat", Llama2Templator, {"messages": data}],
        ["mistralai/Mistral-7B-Instruct-v0.3", MistralTemplator, {"messages": data}],
        ["google/gemma-2-9b-it", GemmaTemplator, {"messages": data}]
    ]

    from transformers import AutoTokenizer
    for tokenizer_path, templator, args in tokenizer_check_list:
        print(f"checking {str(templator)} ...")
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)
        output_from_tokenizer = tokenizer.apply_chat_template(data, tokenize=False).strip()
        output_from_templator = "".join(templator.wrap(**args))
        if output_from_templator != output_from_tokenizer:
            print(f"tokenizer:\n#{output_from_tokenizer}#\n\ntemplator:\n#{output_from_templator}#")

    # structured_input = Qwen2Templator.wrap(data, force_system_prompt=True)
    # structured_input = Llama2Templator.wrap(data)
    # print(structured_input)
    # print("".join(structured_input))
    # exit()

    # from transformers import AutoTokenizer
    # # tokenizer = AutoTokenizer.from_pretrained("/disk/disk_20T/share/Llama-3-8B-Instruct")
    # # tokenizer = AutoTokenizer.from_pretrained("/disk/disk_20T/share/Qwen2-7B")
    # tokenizer = AutoTokenizer.from_pretrained("/disk/disk_20T/qiaoshuofei/PLMs/llama-2-7b-chat")
    # # tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.3")
    # # tokenizer = AutoTokenizer.from_pretrained("google/gemma-2-9b-it")
    
    # print(tokenizer.apply_chat_template(data, tokenize=False))

    # HF_ENDPOINT=https://hf-mirror.com python templator.py