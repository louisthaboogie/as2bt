package com.google.cloud.as2bt;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.IOException;

import java.math.BigInteger;

import java.nio.channels.Channels;
import java.nio.channels.ReadableByteChannel;

import java.util.ArrayList;
import java.util.List;

import org.apache.beam.runners.dataflow.options.DataflowPipelineOptions;
import org.apache.beam.sdk.Pipeline;
import org.apache.beam.sdk.options.Default;
import org.apache.beam.sdk.options.Description;
import org.apache.beam.sdk.options.PipelineOptionsFactory;
import org.apache.beam.sdk.values.PCollection;
import org.apache.beam.sdk.io.FileSystems;
import org.apache.beam.sdk.io.Read;

import org.apache.hadoop.hbase.client.Mutation;
import org.apache.hadoop.hbase.client.Put;
import org.apache.hadoop.hbase.util.Bytes;

import org.apache.beam.sdk.options.ValueProvider;
import org.apache.beam.sdk.transforms.Create;
import org.apache.beam.sdk.transforms.DoFn;
import org.apache.beam.sdk.transforms.ParDo;

import com.google.cloud.bigtable.beam.CloudBigtableIO;
import com.google.cloud.bigtable.beam.CloudBigtableTableConfiguration;

import org.apache.beam.sdk.transforms.Create;
import org.apache.beam.sdk.coders.StringUtf8Coder;

import org.apache.beam.sdk.io.gcp.bigtable.BigtableIO;

import org.apache.beam.sdk.io.TextIO;
import org.apache.beam.sdk.options.ValueProvider;

import org.apache.beam.sdk.coders.SerializableCoder;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

public class DataflowJsonWorker {
    private static final byte[] CF = Bytes.toBytes("info");
  
    private static final String[] JSON_FIELDS = {
        "title", "author", "publishedDate", "imageUrl", "description", "createdBy", "createdById"
    };

    private static final List<byte[]> COLUMNS = new ArrayList<>();

    static {
        for(String field : JSON_FIELDS) {
            COLUMNS.add(Bytes.toBytes(field));
        }
    }

    private static final byte[] ID = Bytes.toBytes("id");
    private static final String NEWLINE = "\\r?\\n";

    private static final JsonParser parser = new JsonParser();
    
    // DoFn implementation that parses JSON and convert to HBase data

    static final DoFn<String, Mutation> MUTATION_TRANSFORM = new DoFn<String, Mutation>() {
        private static final long serialVersionUID = 1L;

        @ProcessElement
        public void processElement(DoFn<String, Mutation>.ProcessContext c) throws Exception {
            String elem = c.element();
           
            JsonObject jsonObj = parser.parse(elem).getAsJsonObject();
            
            String pk = jsonObj.get("id").getAsString();
            String reversed = new StringBuilder(pk).reverse().toString();
            String rowKey = reversed;

            if(jsonObj.has("createdById")) {
                String userId = jsonObj.get("createdById").getAsString().trim();

                if(!userId.isEmpty()) {
                    rowKey += "_" + userId;
                }
            }

            Put put = new Put(rowKey.getBytes());
            put.addColumn(CF, ID, reversed.getBytes());

            for(int i = 0, len = JSON_FIELDS.length; i < len; i++) {
                String jsonField = JSON_FIELDS[i];

                if(jsonObj.has(jsonField)) {
                    put.addColumn(CF, COLUMNS.get(i), jsonObj.get(jsonField).getAsString().getBytes());
                }
            }
    
            c.output(put);
        }
    };
    
    // option for dataflow job
    public static interface As2BtOptions extends DataflowPipelineOptions {
        String getBackupFile();
        void setBackupFile(String backupFile);
        
        String getBigtableName();
        void setBigtableName(String bigtableName);

        String getBigtableInstanceId();
        void setBigtableInstanceId(String bigtableInstanceId);

        String getBigtableTableId();
        void setBigtableTableId(String bigtableTableId);
    }

    // methods for each dataflow job and dataflow template job
    CloudBigtableTableConfiguration setupBigtable(As2BtOptions options) {
        return new CloudBigtableTableConfiguration.Builder()
            .withProjectId(options.getProject())
            .withInstanceId(options.getBigtableInstanceId())
            .withTableId(options.getBigtableTableId())
            .build();   
     }

    CloudBigtableTableConfiguration setupBigtable(DataflowJsonWorkerTemplate.As2BtOptions options) {
        return new CloudBigtableTableConfiguration.Builder()
            .withProjectId(options.getProject())
            .withInstanceId(options.getBigtableInstanceId().get())
            .withTableId(options.getBigtableTableId().get())
            .build();   
     }

    void setupFlow(Pipeline p, As2BtOptions options) throws IOException {
        p
        .apply("ReadFromBackupFile", TextIO.read().from(options.getBackupFile()))
        .apply("TransformParsingsToBigTable", ParDo.of(MUTATION_TRANSFORM))
        .apply("WriteToBigtable", CloudBigtableIO.writeToTable(setupBigtable(options)));
    }

    void setupFlow(Pipeline p, DataflowJsonWorkerTemplate.As2BtOptions options) throws IOException {
        p
        .apply("ReadFromBackupFile", TextIO.read().from(options.getBackupFile()))
        .apply("TransformParsingsToBigTable", ParDo.of(MUTATION_TRANSFORM))
        .apply("WriteToBigtable", CloudBigtableIO.writeToTable(setupBigtable(options)));
    }

    void runAs2Bt(As2BtOptions options) throws IOException {
        System.out.println(options);

        Pipeline p = Pipeline.create(options);
        setupFlow(p, options); 
         
        p.run().waitUntilFinish();
    }

    public static void main(String[] args) throws IOException {
        As2BtOptions options = PipelineOptionsFactory.fromArgs(args).withValidation().as(As2BtOptions.class);
        DataflowJsonWorker worker = new DataflowJsonWorker();

        worker.runAs2Bt(options);
    }
}