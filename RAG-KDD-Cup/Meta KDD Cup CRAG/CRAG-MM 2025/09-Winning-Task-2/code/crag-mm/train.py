#!/usr/bin/env python3

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model
from transformers import (AutoProcessor, MllamaForConditionalGeneration,
                          Trainer, TrainingArguments)


def main():
    # Configuration
    ckpt = "meta-llama/Llama-3.2-11B-Vision-Instruct"
    grad_checkpointing = False

    ds = load_dataset("rbiswasfc/kddcup-sft-datamix")['train'] # multi-task finetuning dataset
    comp_ds = load_dataset("rbiswasfc/kddcup-sft-images")['train'] # images from the competition dataset
    session_ids = comp_ds["session_id"]
    sid2idx = {sid: i for i, sid in enumerate(session_ids)}

    print(f"Dataset loaded: {ds}")
    print(f"Comparison dataset loaded: {comp_ds}")

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=['down_proj','o_proj','k_proj','q_proj','gate_proj','up_proj','v_proj'],
        use_dora=False,
        init_lora_weights="gaussian"
    )
    
    model = MllamaForConditionalGeneration.from_pretrained(ckpt, torch_dtype=torch.bfloat16)
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    if grad_checkpointing:
        model.gradient_checkpointing_enable()
        print("Gradient checkpointing enabled")

    processor = AutoProcessor.from_pretrained(ckpt)
    
    def process(examples, max_tokens=3072, max_char_in_answer=1024):        
        texts = [f"{example['prompt']}\n\n{example['answer'][:max_char_in_answer]}<|eot_id|>" for example in examples]
        images = [[comp_ds[sid2idx[example["session_id"]]]["image"].convert("RGB")] for example in examples]
        
        # Pre-truncate texts if needed
        truncated_texts = []
        prompt_lengths_after_truncation = []
        
        for idx, text in enumerate(texts):
            # Tokenize to check length
            tokens = processor.tokenizer(text, add_special_tokens=False)
            token_ids = tokens["input_ids"]
            
            if len(token_ids) > max_tokens:
                # Truncate from left
                token_ids = token_ids[-max_tokens:]
                truncated_text = processor.tokenizer.decode(token_ids, skip_special_tokens=False)
                
                # Calculate new prompt length after truncation
                prompt_text = f"{examples[idx]['prompt']}\n\n"
                prompt_tokens = processor.tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
                original_prompt_length = len(prompt_tokens)
                truncation_amount = len(tokens["input_ids"]) - max_tokens
                new_prompt_length = max(0, original_prompt_length - truncation_amount)
                
                truncated_texts.append(truncated_text)
                prompt_lengths_after_truncation.append(new_prompt_length)
            else:
                truncated_texts.append(text)
                # Calculate prompt length for non-truncated text
                prompt_text = f"{examples[idx]['prompt']}\n\n"
                prompt_tokens = processor.tokenizer(prompt_text, add_special_tokens=False)["input_ids"]
                prompt_lengths_after_truncation.append(len(prompt_tokens))
        
        # Process with truncated texts
        batch = processor(text=truncated_texts, images=images, return_tensors="pt", padding=True, add_special_tokens=False)
        
        # Create labels and mask prompt tokens
        labels = batch["input_ids"].clone()
        
        # Mask prompt tokens based on pre-calculated lengths
        for idx, prompt_length in enumerate(prompt_lengths_after_truncation):
            if prompt_length > 0:
                labels[idx, :prompt_length] = -100
        
        # Also mask padding and special tokens
        labels[labels == processor.tokenizer.pad_token_id] = -100 
        labels[labels == 128256] = -100
        
        batch["labels"] = labels
        batch = {k: v.to(torch.bfloat16) if v.dtype == torch.float32 else v for k, v in batch.items()}
        
        return batch
    
    # Training arguments optimized for 8 GPUs
    args = TrainingArguments(
        num_train_epochs=1,
        remove_unused_columns=False,
        per_device_train_batch_size=1,   # Increased from 1 to 2 for A100s
        gradient_accumulation_steps=4,   # Reduced from 4 to 1 (8 GPUs * 2 batch size = 16 effective)
        warmup_steps=32,                 # Increased warmup steps
        learning_rate=1e-5,
        weight_decay=1e-6,
        adam_beta2=0.99,
        logging_steps=1,                 # Increased logging interval
        save_strategy="steps",           # Changed to save checkpoints
        save_steps=400,                  # Save every 500 steps
        save_total_limit=3,              # Keep last 2 checkpoints
        optim="adamw_8bit",
        push_to_hub=False,
        bf16=True,
        fp16=False,                      # Explicitly set to False since using bf16
        output_dir="./models",
        dataloader_pin_memory=False,
        report_to="wandb",
        dataloader_num_workers=8,
        ddp_find_unused_parameters=False,
        gradient_checkpointing=grad_checkpointing,     # Enable gradient checkpointing
        max_grad_norm=10.0,
        lr_scheduler_type="cosine",
    )
    
    # Initialize trainer
    trainer = Trainer(model=model, train_dataset=ds, data_collator=process, args=args)
    
    # Start training
    trainer.train()

if __name__ == "__main__":
    main()

# accelerate launch --num_processes=8 train.py