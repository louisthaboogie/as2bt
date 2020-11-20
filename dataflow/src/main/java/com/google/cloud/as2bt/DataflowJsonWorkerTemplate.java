package com.google.cloud.as2bt;

import java.io.IOException;

import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;

import org.apache.beam.sdk.options.ValueProvider;
import org.apache.beam.sdk.PipelineResult;

public class DataflowJsonWorkerTemplate {
    private DataflowJsonWorker worker;

    public DataflowJsonWorkerTemplate() {
        worker = new DataflowJsonWorker();
    }

    // options for Dataflow template 
    public static interface As2BtOptions extends DataflowPipelineOptions {
        ValueProvider<String> getBackupFile();
        void setBackupFile(ValueProvider<String> backupFile);

        ValueProvider<String> getBigtableName();
        void setBigtableName(ValueProvider<String> bigtableName);

        ValueProvider<String> getBigtableInstanceId();
        void setBigtableInstanceId(ValueProvider<String> bigtableInstanceId);

        ValueProvider<String> getBigtableTableId();
        void setBigtableTableId(ValueProvider<String> bigtableTableId);
    }
    
    void runAs2Bt(As2BtOptions options) throws IOException {
        System.out.println(options);
        Pipeline p = Pipeline.create(options);

        worker.setupFlow(p, options); 
        PipelineResult result = p.run();
        
        // for template 
        if (options.getTemplateLocation() == null) {
            result.waitUntilFinish();
        }
    }

    public static void main(String[] args) throws IOException {
        DataflowJsonWorkerTemplate workerTemplate = new DataflowJsonWorkerTemplate();
        As2BtOptions options = PipelineOptionsFactory.fromArgs(args).as(As2BtOptions.class);

        workerTemplate.runAs2Bt(options);
    }
}