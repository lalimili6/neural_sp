#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Define evaluation method by Word Error Rate (Librispeech corpus)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from tqdm import tqdm

from utils.io.labels.word import Idx2word
from utils.io.variable import np2var
from utils.evaluation.edit_distance import compute_wer, wer_align


def do_eval_wer(model, model_type, dataset, label_type, data_size, beam_width,
                is_test=False, eval_batch_size=None, progressbar=False):
    """Evaluate trained model by Word Error Rate.
    Args:
        model: the model to evaluate
        model_type (string): ctc or attention
        dataset: An instance of a `Dataset' class
        label_type (string): character or character_capital_divide or
            word_freq1 or word_freq5 or word_freq10 or word_freq15
        data_size (string): 100h or 460h or 960h
        beam_width: (int): the size of beam
        is_test (bool, optional): set to True when evaluating by the test set
        eval_batch_size (int, optional): the batch size when evaluating the model
        progressbar (bool, optional): if True, visualize the progressbar
    Returns:
        wer_mean (float): An average of WER
    """
    batch_size_original = dataset.batch_size

    # Reset data counter
    dataset.reset()

    # Set batch size in the evaluation
    if eval_batch_size is not None:
        dataset.batch_size = eval_batch_size

    vocab_file_path = '../metrics/vocab_files/' + \
        label_type + '_' + data_size + '.txt'

    idx2word = Idx2word(vocab_file_path)

    wer_mean = 0
    if progressbar:
        pbar = tqdm(total=len(dataset))
    for data, is_new_epoch in dataset:

        # Create feed dictionary for next mini-batch
        if model_type in ['ctc', 'attention']:
            inputs, labels, inputs_seq_len, labels_seq_len, _ = data
        elif model_type in ['hierarchical_ctc', 'hierarchical_attention']:
            inputs, labels, _, inputs_seq_len, labels_seq_len, _, _ = data
        else:
            raise TypeError

        # Wrap by variable
        inputs = np2var(inputs, use_cuda=model.use_cuda, volatile=True)
        inputs_seq_len = np2var(
            inputs_seq_len, use_cuda=model.use_cuda, volatile=True, dtype='int')

        batch_size = inputs[0].size(0)

        # Decode
        if model_type == 'attention':
            labels_pred, _ = model.decode_infer(
                inputs[0], inputs_seq_len[0], beam_width=beam_width)
        elif model_type == 'ctc':
            logits, perm_indices = model(inputs[0], inputs_seq_len[0])
            labels_pred = model.decode(
                logits, inputs_seq_len[0][perm_indices], beam_width=beam_width)
            labels_pred -= 1
            # NOTE: index 0 is reserved for blank

        for i_batch in range(batch_size):

            # Convert from list of index to string
            if is_test:
                word_list_true = labels[0][i_batch][0].split('_')
                # NOTE: transcript is seperated by space('_')
            else:
                if model_type in ['ctc', 'hierarchical_ctc']:
                    word_list_true = idx2word(
                        labels[0][i_batch][:labels_seq_len[0][i_batch]])
                elif model_type in ['attention', 'hierarchical_attention']:
                    word_list_true = idx2word(
                        labels[0][i_batch][1:labels_seq_len[0][i_batch] - 1])
                    # NOTE: Exclude <SOS> and <EOS>
            word_list_pred = idx2word(labels_pred[i_batch])
            # NOTE: Trancate by the first <EOS>

            # Compute WER
            wer_mean += compute_wer(ref=word_list_true,
                                    hyp=word_list_pred,
                                    normalize=True)
            # substitute, insert, delete = wer_align(
            #     ref=str_pred.split('_'),
            #     hyp=str_true.split('_'))
            # print('SUB: %d' % substitute)
            # print('INS: %d' % insert)
            # print('DEL: %d' % delete)

            if progressbar:
                pbar.update(1)

        if is_new_epoch:
            break

    wer_mean /= len(dataset)

    # Register original batch size
    if eval_batch_size is not None:
        dataset.batch_size = batch_size_original

    return wer_mean
