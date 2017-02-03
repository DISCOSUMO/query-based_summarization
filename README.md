# query-based_summarization

This repository contains a module for query-focused summarization of discussion threads in the DISCOSUMO project. It takes two input arguments: 
- a directory of threads
- a tab-separated file of the format `query,clicked title,threadid`

It implements Maximal Marginal Relevance (MMR) for a query-thread pair, and scores the posts in a thread using MMR. 

The input format is highly specific for the DISCOSUMO project but the implementation of MMR might be reusable in other contexts.