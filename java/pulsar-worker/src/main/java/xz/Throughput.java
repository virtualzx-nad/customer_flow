package xz;

import java.time.Instant;
import java.time.Duration;
import java.util.concurrent.CompletableFuture;

import org.apache.pulsar.functions.api.Context;
import org.apache.pulsar.functions.api.Function;
import org.apache.pulsar.client.api.TypedMessageBuilder;
import org.apache.pulsar.client.api.Schema;
import org.apache.pulsar.client.api.PulsarClient;
import org.apache.pulsar.client.api.Producer;


import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class Throughput implements Function<String, String> {
    private static final Logger logger = LoggerFactory.getLogger(Throughput.class);

    public String process(String trigger, Context context) {
        String topic = (String) context.getUserConfigValueOrDefault("topic", "throughput-topic");
        String s = (String) context.getUserConfigValueOrDefault("message", "my-test-message");
        long n_message = (long) context.getUserConfigValueOrDefault("n_message", 10000);
        String url = (String) context.getUserConfigValueOrDefault("serviceUrl", "pulsar://localhost:6650");
        // Initialize a client and producer on the target topic
        logger.info("Creating my own producer.");
        PulsarClient client=null;
        Producer<byte[]> producer=null;
        try{
            client = PulsarClient.builder()
                .serviceUrl(url)
                .build();
            producer = client.newProducer()
                .topic(topic)
                .blockIfQueueFull(true)
                .enableBatching(true)
                .create();
        }catch(Exception e){
            logger.warn("Failed to create producer.");
        }
        logger.info("Performing throughput test");
        // Do the throughput test.
        Instant start = Instant.now();
        int nfail = 0;
        for(int i=0; i<n_message; i++){
            try{
                producer.sendAsync("my-async-message".getBytes());
            }catch(Exception ex){
                logger.warn("Message failed to sent" + ex);
                nfail += 1;
            }        
        }
        if(nfail>0) logger.warn("Number of failed sends: {}", nfail);
        logger.info("Flushing messages in producer queue");
        try{
            producer.flush();
        }catch(Exception ex){
            logger.warn("Error flushing producer message queue: "+ex);
        }
        Instant finish = Instant.now();
        logger.info("Done");
        double timeElapsed = Duration.between(start, finish).toMillis() / 1.0e3;
        double throughput = n_message/timeElapsed;
        // Close the client and producer
        producer.closeAsync()
            .thenRun(() -> logger.info("Producer closed"))
            .exceptionally((ex) -> {
                logger.warn("Failed to close producer: " + ex);
                return null;
            });
        client.closeAsync()
            .thenRun(() -> logger.info("Pulsar client closed"))
            .exceptionally((ex) -> {
                logger.warn("Failed to close client: " + ex);
                return null;
            });;

        return String.format("My throughput is %12.2f msg/sec", throughput);
    }
}