package xz;

import java.time.Instant;
import java.time.Duration;

import org.apache.pulsar.client.api.PulsarClient;
import org.apache.pulsar.client.api.Producer;
import org.apache.pulsar.client.api.MessageId;


import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


/**
 * Hello world!
 *
 */
public class App 
{
    private static final Logger logger = LoggerFactory.getLogger(App.class);

    public static void main( String[] args )
    {
        logger.info( "Pulsar throughput test in java." );
        PulsarClient client=null;
        Producer<byte[]> producer=null;
        try{
            client = PulsarClient.builder()
                .serviceUrl("pulsar://localhost:6650")
                .build();
            producer = client.newProducer()
                .topic("my-topic")
                .blockIfQueueFull(true)
                .enableBatching(true)
                .create();
        }catch(Exception e){
            logger.warn("Failed to create producer.");
        }
        /* producer.sendAsync("my-async-message".getBytes()).thenAccept(msgId -> {
            System.out.printf("Message with ID %s successfully sent", msgId);
        });*/
        Instant start = Instant.now();
        int nfail = 0;
        long n_message = 10000;
        for(int i=0; i<n_message; i++){
            try{
                producer.sendAsync("my-async-message".getBytes());
            }catch(Exception ex){
                logger.warn("Message failed to sent" + ex);
                nfail += 1;
            }        
        }
        if(nfail>0) logger.warn("Number of failed sends: {}", nfail);
        try{
            producer.flush();
        }catch(Exception ex){
            logger.warn("Error flushing producer message queue: "+ex);
        }
        Instant finish = Instant.now();
        double timeElapsed = Duration.between(start, finish).toMillis() / 1.0e3;
        logger.info("Processed {} messages in {} sec", n_message, timeElapsed);
        logger.info("Throughput: {} msg/sec", n_message/timeElapsed);
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

    }
}
